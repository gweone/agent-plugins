"""Static provider registration and helper protocol checks, not native runtime tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

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

    def test_cursor_explicit_readonly_wrappers_share_roles_and_references(self):
        manifest = self.manifest("cursor")
        expected = ["./agents/cursor/knowledge-extractor.md",
                    "./agents/cursor/knowledge-reviewer.md"]
        self.assertEqual(manifest["agents"], expected)
        self.assertNotIn("hooks", manifest)
        for relative in expected:
            path = BASE / relative
            text = path.read_text()
            frontmatter = text.split("---", 2)[1]
            self.assertRegex(frontmatter, r"(?m)^name: knowledge-(extractor|reviewer)$")
            self.assertRegex(frontmatter, r"(?m)^description: .+$")
            self.assertRegex(frontmatter, r"(?m)^readonly: true$")
            self.assertNotRegex(frontmatter, r"(?m)^tools:")
            role = "../" + path.name
            self.assertIn(role, text)
            self.assertTrue((path.parent / role).is_file())
            self.assertIn("../../references/protocol.md", text)
            self.assertTrue((path.parent / "../../references/protocol.md").is_file())
            self.assertIn("parent", text)
            self.assertIn("Never", text)
        reviewer = (BASE / expected[1]).read_text()
        self.assertIn("../../references/review-rubric.md", reviewer)

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
