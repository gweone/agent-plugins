"""Offline packaging/helper tests; prompt scenarios are coverage, not model execution."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
HELPER = BASE / "hooks/context.py"


class HookTests(unittest.TestCase):
    def run_hook(self, data, enabled=False):
        env = dict(os.environ)
        env.pop("SHARPPS_KNOWLEDGE_STOP_REMINDER", None)
        if enabled:
            env["SHARPPS_KNOWLEDGE_STOP_REMINDER"] = "1"
        result = subprocess.run([sys.executable, "-I", "-B", str(HELPER)], input=data,
                                capture_output=True, env=env, timeout=3, check=True)
        self.assertEqual(result.stderr, b"")
        self.assertLess(len(result.stdout), 1500)
        return json.loads(result.stdout) if result.stdout else None

    def test_context_only_events_ignore_task_and_paths(self):
        for event in ("SessionStart", "UserPromptSubmit"):
            result = self.run_hook(json.dumps({"hook_event_name": event,
                "prompt": "sensitive-marker", "transcript_path": "/must/not/open"}).encode())
            specific = result["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], event)
            self.assertNotIn("sensitive-marker", json.dumps(result))
            self.assertNotIn("/must/not/open", json.dumps(result))
            self.assertEqual(set(result), {"hookSpecificOutput"})

    def test_stop_default_off_and_nonblocking_opt_in(self):
        data = b'{"hook_event_name":"Stop","stop_hook_active":false}'
        self.assertIsNone(self.run_hook(data))
        self.assertEqual(set(self.run_hook(data, enabled=True)), {"systemMessage"})

    def test_stop_recursion_and_unknown_guard(self):
        for guard in (True, None, "false", 0):
            data = json.dumps({"hook_event_name":"Stop", "stop_hook_active":guard}).encode()
            self.assertIsNone(self.run_hook(data, enabled=True))
        self.assertIsNone(self.run_hook(b'{"hook_event_name":"Stop"}', True))

    def test_malformed_oversized_and_unknown_are_silent(self):
        for data in (b"", b"{", b"[]", b"null", b"\xff", b" " * 16385,
                     b'{"hook_event_name":"PermissionRequest"}', b"[" * 3000):
            self.assertIsNone(self.run_hook(data, enabled=True))

    def test_helper_has_no_network_files_or_transcript_operations(self):
        tree = ast.parse(HELPER.read_text())
        imports = {a.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                   for a in node.names}
        self.assertEqual(imports, {"json", "os", "sys"})
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id in {"open", "eval", "exec", "compile"}
                             for n in ast.walk(tree)))
        self.assertNotIn("transcript_path", HELPER.read_text())


class PackageTests(unittest.TestCase):
    def test_json_strict_and_shared_provider_paths(self):
        def no_duplicates(pairs):
            result = {}
            for key, value in pairs:
                self.assertNotIn(key, result)
                result[key] = value
            return result
        for path in BASE.rglob("*.json"):
            json.loads(path.read_text(), object_pairs_hook=no_duplicates)
        for provider in ("claude", "codex", "cursor", "grok", "opencode"):
            folder = BASE / f".{provider}-plugin"
            manifest = json.loads((folder / "plugin.json").read_text())
            self.assertEqual(manifest["name"], "sharpps-knowledge")
            self.assertEqual(manifest["version"], "0.1.0")
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertEqual(list(folder.iterdir()), [folder / "plugin.json"])
            self.assertNotIn("mcpServers", manifest)

    def test_registration(self):
        for relative, source in ((".claude-plugin/marketplace.json", "./plugin/sharpps-knowledge"),
                                 (".cursor-plugin/marketplace.json", "plugin/sharpps-knowledge")):
            entries = json.loads((ROOT / relative).read_text())["plugins"]
            matches = [e for e in entries if e["name"] == "sharpps-knowledge"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["source"], source)
        entries = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())["plugins"]
        matches = [e for e in entries if e["name"] == "sharpps-knowledge"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["source"], {"source":"local", "path":"./plugin/sharpps-knowledge"})
        self.assertEqual(json.loads((ROOT / "opencode.json").read_text())["skills"].count(
            "./plugin/sharpps-knowledge/skills"), 1)

    def test_canonical_frontmatter_and_reference_links(self):
        # Reproduce the inspected validator's read-only frontmatter checks without
        # executing its misleadingly named installation command.
        all_skills = list((ROOT / "plugin").glob("*/skills/*/SKILL.md"))
        self.assertGreater(len(all_skills), 5)
        for path in all_skills:
            text = path.read_text()
            self.assertEqual(text.splitlines()[0], "---", str(path))
            self.assertRegex(text, r"(?m)^name:")
            self.assertRegex(text, r"(?m)^description:")
        self.assertEqual(len(list((BASE / "skills").glob("*/SKILL.md"))), 5)
        for path in BASE.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target:
                    self.assertTrue((path.parent / target).is_file(), f"{path}: {target}")

    def test_traditional_hooks_and_readonly_agents(self):
        manifest = json.loads((BASE / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(set(manifest["agents"]),
                         {"./" + str(path.relative_to(BASE))
                          for path in (BASE / "agents").glob("*.md")})
        self.assertEqual(len(manifest["agents"]), 2)
        self.assertEqual(manifest["hooks"], "./hooks/knowledge-hooks.json")
        self.assertFalse((BASE / "hooks/hooks.json").exists())
        hooks = json.loads((BASE / manifest["hooks"]).read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit", "Stop"})
        for groups in hooks.values():
            self.assertEqual(len(groups), 1)
            command = groups[0]["hooks"][0]
            self.assertEqual(command["type"], "command")
            self.assertEqual(command["timeout"], 2)
            self.assertEqual(command["command"], 'python3 -I "${CLAUDE_PLUGIN_ROOT}/hooks/context.py"')
        for path in (BASE / "agents").glob("*.md"):
            self.assertRegex(path.read_text(), r"(?m)^tools: Read$")
            self.assertIn("parent", path.read_text())

    def test_incomplete_review_input_guard_static_coverage(self):
        # This checks prompt/contract coverage, not model or backend behavior.
        for relative in ("references/protocol.md", "references/review-rubric.md",
                         "references/backend-contract.md", "skills/knowledge-review/SKILL.md"):
            text = (BASE / relative).read_text()
            self.assertIn("summary_truncated", text)
            self.assertIn("incomplete", text)
            self.assertIn("escalate", text)
        contract = (BASE / "references/backend-contract.md").read_text()
        self.assertIn("review_input_incomplete", contract)
        self.assertIn("2,000", contract)
        self.assertIn("100-item cap", contract)
        self.assertIn("Manual review is unchanged", contract)
        self.assertIn("approved_for_reuse", contract)
        self.assertIn("evidence_supported", contract)
        self.assertIn("without connector replay", contract)

    def test_scenario_protocol_coverage_not_behavioral_execution(self):
        fixture = json.loads((BASE / "tests/scenarios.json").read_text())
        self.assertIn("unrun model-behavior", fixture["kind"])
        protocol = (BASE / "references/protocol.md").read_text()
        self.assertEqual(len({s["id"] for s in fixture["scenarios"]}), 40)
        for scenario in fixture["scenarios"]:
            self.assertTrue(scenario["expected_behavior"])
            for phrase in scenario["protocol_checks"]:
                self.assertIn(phrase, protocol, scenario["id"])


class WorkspaceProtocolTests(unittest.TestCase):
    """Static prompt contracts and real fixed hook output, not server/model tests."""

    def text(self, relative):
        return (BASE / relative).read_text()

    def test_live_resolver_schema_and_identity_boundaries(self):
        protocol = self.text("references/protocol.md")
        for phrase in ("knowledge_resolve_workspace", "WorkspaceResolveRequest",
                       "required `workspace_path`", "required `workspace_namespace`",
                       "strict boolean `create_if_missing` (default true)",
                       "scope: 'workspace'", "owner comes solely from the authenticated principal",
                       "Namespace is a client-supplied selector", "ASCII slug",
                       "128 characters", "4,096 bytes", "POSIX absolute or Windows drive absolute",
                       "No web approval or manual project_id", "Live schema discovery overrides",
                       "not a client name, plugin directory, retrieved text",
                       "Do not auto-adopt existing `project.workspace` metadata",
                       "Do not derive IDs", "executor workspace registration"):
            self.assertIn(phrase, protocol)
        self.assertNotIn("knowledge_list_projects", protocol)

    def test_scope_lifecycle_defaults_and_shared_creation_gates(self):
        protocol = self.text("references/protocol.md")
        for phrase in ("project IDs override automatic workspace resolution",
                       "discard the old automatic scope", "Explicit scopes remain pinned",
                       "older server", "ask for explicit authorized project IDs",
                       "never bypass it using another connector, namespace or scope",
                       "including workspace/collection creation", "learning defaults OFF",
                       "Persisted automatic-review consent also defaults OFF",
                       "knowledge_set_learning", "enabling either does not enable the other",
                       "knowledge_collection_list", "knowledge_collection_create",
                       "Explicit conversational requests to create a collection",
                       "Collection creation is not publication or grants",
                       "never internet anonymous public knowledge",
                       "never delete/recreate a workspace or collection as fallback",
                       "knowledge_list_workspaces", "limit at most 50"):
            self.assertIn(phrase, protocol)

    def test_skill_branches_and_recent_search_are_consistent(self):
        setup = self.text("skills/knowledge-setup/SKILL.md")
        retrieve = self.text("skills/knowledge-retrieve/SKILL.md")
        status = self.text("skills/knowledge-status/SKILL.md")
        learn = self.text("skills/knowledge-learn/SKILL.md")
        self.assertIn("knowledge_resolve_workspace", setup)
        self.assertIn("older-server fallback needs explicit authorized IDs", retrieve)
        self.assertIn("re-resolve the automatic scope", retrieve)
        self.assertIn("sort: 'recent'", retrieve)
        self.assertIn("empty query is permitted only with recent sort", retrieve)
        self.assertIn("knowledge_list_workspaces", status)
        self.assertIn("Status is read-only", status)
        self.assertIn("knowledge_set_learning", learn)
        self.assertIn("not enablement or evidence-sharing consent", learn)
        for relative in ("README.md", "references/capabilities.md"):
            text = self.text(relative)
            self.assertIn("namespace", text)
            self.assertIn("OFF", text)
            self.assertIn("curated collections", text)
        capabilities = self.text("references/capabilities.md")
        self.assertIn("`skills.paths`", capabilities)
        self.assertIn("None claimed", capabilities)
        self.assertNotIn("skills array", capabilities)

    def test_hook_fixed_context_ignores_workspace_and_namespace_input(self):
        hook = HookTests()
        outputs = []
        for selector in ("untrusted-path-one", "untrusted-path-two"):
            outputs.append(hook.run_hook(json.dumps({
                "hook_event_name": "SessionStart", "cwd": selector,
                "workspace_namespace": selector, "hostname": selector,
                "prompt": selector, "transcript_path": selector,
            }).encode()))
        self.assertEqual(outputs[0], outputs[1])
        context = outputs[0]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("required stable nonsecret host machine namespace", context)
        self.assertIn("learning/review consent default OFF", context)
        self.assertIn("collection creation needs explicit request", context)
        self.assertNotIn("untrusted-path", context)
        tree = ast.parse(HELPER.read_text())
        env_gets = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and ast.unparse(n.func) == "os.environ.get"]
        self.assertEqual(len(env_gets), 1)
        self.assertEqual(env_gets[0].args[0].value, "SHARPPS_KNOWLEDGE_STOP_REMINDER")
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr in
                             {"getcwd", "uname", "hostname", "stat", "read_text", "resolve"}
                             for n in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
