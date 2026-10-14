"""Static provider registration and helper protocol checks, not native runtime tests."""
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

BASE = Path(__file__).resolve().parents[1]


class ProviderRegistrationTests(unittest.TestCase):
    def manifest(self, provider):
        return json.loads((BASE / f".{provider}-plugin/plugin.json").read_text())

    def test_codex_explicit_shared_hooks_without_unsupported_agents(self):
        manifest = self.manifest("codex")
        self.assertEqual(manifest["hooks"], "./hooks/knowledge-hooks.json")
        self.assertNotIn("agents", manifest)
        hooks = json.loads((BASE / manifest["hooks"]).read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit", "Stop"})
        for groups in hooks.values():
            self.assertEqual(len(groups), 1)
            command = groups[0]["hooks"][0]
            self.assertEqual(command["type"], "command")
            self.assertEqual(command["timeout"], 2)
            self.assertEqual(command["command"], 'python3 -I "${CLAUDE_PLUGIN_ROOT}/hooks/context.py"')

    def test_codex_helper_documented_output_shapes_and_silent_success(self):
        # OpenAI documents empty stdout on exit 0 as success, including Stop.
        env = dict(os.environ)
        env.pop("SHARPPS_KNOWLEDGE_STOP_REMINDER", None)
        for event in ("SessionStart", "UserPromptSubmit", "Stop"):
            payload = {"hook_event_name": event, "stop_hook_active": False,
                       "prompt": "secret-marker", "transcript_path": "/do/not/read"}
            result = subprocess.run([sys.executable, "-I", "-B", str(BASE / "hooks/context.py")],
                                    input=json.dumps(payload).encode(), capture_output=True,
                                    env=env, timeout=3, check=True)
            self.assertEqual(result.stderr, b"")
            if event == "Stop":
                self.assertEqual(result.stdout, b"")
            else:
                output = json.loads(result.stdout)
                self.assertEqual(set(output), {"hookSpecificOutput"})
                specific = output["hookSpecificOutput"]
                self.assertEqual(set(specific), {"hookEventName", "additionalContext"})
                self.assertEqual(specific["hookEventName"], event)
                self.assertNotIn("secret-marker", specific["additionalContext"])
                self.assertNotIn("/do/not/read", specific["additionalContext"])
        env["SHARPPS_KNOWLEDGE_STOP_REMINDER"] = "1"
        result = subprocess.run([sys.executable, "-I", "-B", str(BASE / "hooks/context.py")],
                                input=b'{"hook_event_name":"Stop","stop_hook_active":false}',
                                capture_output=True, env=env, timeout=3, check=True)
        self.assertEqual(set(json.loads(result.stdout)), {"systemMessage"})

    def test_cursor_explicit_readonly_self_contained_roles(self):
        manifest = self.manifest("cursor")
        expected = ["./agents/cursor-knowledge-extractor.md",
                    "./agents/cursor-knowledge-reviewer.md"]
        self.assertEqual(manifest["agents"], expected)
        self.assertNotIn("hooks", manifest)
        for relative, role in zip(expected, ("extractor", "reviewer")):
            path = BASE / relative
            self.assertTrue(path.is_file())
            self.assertEqual(path.parent, BASE / "agents")
            text = path.read_text()
            frontmatter = text.split("---", 2)[1]
            self.assertRegex(frontmatter, r"(?m)^name: knowledge-(extractor|reviewer)$")
            self.assertRegex(frontmatter, r"(?m)^description: .+$")
            self.assertRegex(frontmatter, r"(?m)^readonly: true$")
            self.assertNotRegex(frontmatter, r"(?m)^tools:")
            shared = (BASE / f"agents/knowledge-{role}.md").read_text()
            self.assertEqual(text.split("---", 2)[2], shared.split("---", 2)[2])
            self.assertIn("no external reference Reads are required", text)
            self.assertIn("parent", text)
            self.assertIn("Never", text)
            # Compatibility files are preserved, but never registered.
            legacy = BASE / f"agents/cursor/knowledge-{role}.md"
            self.assertTrue(legacy.is_file())
            self.assertNotIn("./" + legacy.relative_to(BASE).as_posix(), expected)

    @unittest.skipUnless(shutil.which("zip") and shutil.which("python3"),
                         "packaging script requires zip and python3")
    def test_real_package_contains_manifest_targets_and_flattened_cursor_files(self):
        # Execute the unchanged script only in a disposable repository-shaped fixture.
        # This exercises ZIP contents, not host installation, syncing or model behavior.
        root = BASE.parents[1]
        if not (root / "scripts/package-plugins.sh").is_file():
            self.skipTest("optional locally untracked packaging script is absent")
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / "scripts").mkdir()
            script = fixture / "scripts/package-plugins.sh"
            shutil.copy2(root / "scripts/package-plugins.sh", script)
            source = fixture / "plugin/sharpps-knowledge"
            shutil.copytree(BASE, source,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            result = subprocess.run(["bash", str(script)], cwd=fixture,
                                    env={"PATH": os.defpath}, capture_output=True,
                                    text=True, timeout=30, check=True)
            self.assertIn("packaged 1 plugin(s)", result.stdout)
            version = self.manifest("codex")["version"]
            archives = list((fixture / "artifacts").glob("*.zip"))
            self.assertEqual([p.name for p in archives],
                             [f"sharpps-knowledge-{version}.zip"])
            with zipfile.ZipFile(archives[0]) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertFalse(any("__pycache__" in n or n.endswith(".pyc")
                                     for n in names))

                def require_file(relative):
                    path = PurePosixPath(relative)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    member = "sharpps-knowledge/" + path.as_posix()
                    self.assertIn(member, names)
                    self.assertFalse(archive.getinfo(member).is_dir())
                    self.assertEqual(archive.read(member), (source / path).read_bytes())

                for provider in ("claude", "codex", "cursor", "grok", "opencode"):
                    manifest_path = f".{provider}-plugin/plugin.json"
                    require_file(manifest_path)
                    manifest = json.loads(archive.read("sharpps-knowledge/" + manifest_path))
                    for target in manifest.get("agents", []):
                        require_file(target)
                    if "hooks" in manifest:
                        require_file(manifest["hooks"])
                    skills = source / manifest["skills"]
                    self.assertTrue(skills.is_dir())
                    skill_files = [p for p in skills.rglob("*") if p.is_file()]
                    self.assertTrue(skill_files)
                    for path in skill_files:
                        require_file(path.relative_to(source).as_posix())
                for relative in ("agents/cursor-knowledge-reviewer.md",
                                 "agents/cursor-knowledge-extractor.md",
                                 "agents/cursor/knowledge-reviewer.md",
                                 "agents/cursor/knowledge-extractor.md",
                                 "agents/knowledge-reviewer.md", "agents/knowledge-extractor.md",
                                 "references/protocol.md", "references/review-rubric.md",
                                 "references/backend-contract.md", "hooks/context.py"):
                    require_file(relative)
                # Prove this assertion detects a missing flattened target, rather than
                # merely accepting the manifest's mention of that path.
                names.remove("sharpps-knowledge/agents/cursor-knowledge-reviewer.md")
                with self.assertRaises(AssertionError):
                    require_file("agents/cursor-knowledge-reviewer.md")

    def test_unverified_or_documentation_only_manifests_do_not_claim_native_parity(self):
        for provider in ("grok", "opencode"):
            manifest = self.manifest(provider)
            self.assertNotIn("agents", manifest)
            self.assertNotIn("hooks", manifest)
        for provider in ("codex", "cursor", "grok", "opencode"):
            folder = BASE / f".{provider}-plugin"
            self.assertEqual(list(folder.iterdir()), [folder / "plugin.json"])
            self.assertNotIn("mcpServers", self.manifest(provider))


if __name__ == "__main__":
    unittest.main()
