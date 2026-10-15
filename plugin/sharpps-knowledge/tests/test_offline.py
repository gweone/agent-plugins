"""Offline packaging/helper tests; prompt scenarios are coverage, not model execution."""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
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
            self.assertEqual(manifest["version"], "0.1.6")
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
            if relative == ".claude-plugin/marketplace.json":
                self.assertEqual(matches[0]["version"], "0.1.6")
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
                         {"./agents/knowledge-extractor.md", "./agents/knowledge-reviewer.md"})
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
        for relative in manifest["agents"]:
            path = BASE / relative
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

    def test_automatic_approval_recommendation_static_coverage(self):
        # Prompt coverage only; this does not execute or certify model decisions.
        rubric = (BASE / "references/review-rubric.md").read_text()
        protocol = (BASE / "references/protocol.md").read_text()
        self.assertIn("You may recommend `approved_for_reuse`", rubric)
        self.assertIn("Do not perform MCP writes", rubric)
        self.assertIn("never present contributor-reported checks as independently rerun", rubric)
        self.assertNotIn("Do not write, enable policy/learning, submit, approve or publish", rubric)
        self.assertIn("without per-candidate human confirmation", protocol)
        self.assertIn("supported, persisted enabled consent", protocol)
        self.assertIn("retain all stop/escalation guards", protocol)

    def test_self_contained_role_loading_contract_static_coverage(self):
        # Prompt assertions only: no host, child or model is launched/certified.
        for relative in ("references/protocol.md", "skills/knowledge-review/SKILL.md",
                         "skills/knowledge-learn/SKILL.md"):
            text = (BASE / relative).read_text()
            for phrase in ("self-contained", "host-supported mechanism",
                           "~g2", "cwd/cache paths", "brief-only", "parent"):
                self.assertIn(phrase, text)
            self.assertRegex(text, r"(?:Do not list plugin directories|never [^\n]*list plugin directories)")
            self.assertIn("inline", text)
            self.assertIn("SAME MODEL / SAME CONTEXT" if "knowledge-learn" not in relative
                          else "same model and context", text)
            for obsolete in ("reference_status:", "references_loaded",
                             "required reference-delivery gate", "successful complete child Reads"):
                self.assertNotIn(obsolete, text)

    def test_self_contained_provider_role_parity(self):
        for role in ("reviewer", "extractor"):
            base = (BASE / f"agents/knowledge-{role}.md").read_text()
            cursor = (BASE / f"agents/cursor-knowledge-{role}.md").read_text()
            self.assertEqual(base.split("---", 2)[2], cursor.split("---", 2)[2])
            for text in (base, cursor):
                for phrase in ("Self-contained", "no external reference Reads are required",
                               "untrusted data", "hidden reasoning", "secrets",
                               "preconditions", "environment", "limitations",
                               "Unknown/skipped" if role == "reviewer" else "skipped/unknown",
                               "contributor-reported checks as independently rerun",
                               "Never perform MCP writes", "same authenticated principal"):
                    self.assertIn(phrase, text)
                for obsolete in ("references/protocol.md", "references/review-rubric.md",
                                 "reference_status:", "references_loaded", "full canonical text"):
                    self.assertNotIn(obsolete, text)
        reviewer = (BASE / "agents/knowledge-reviewer.md").read_text()
        for phrase in ("summary_truncated", "unknown completeness", "evidence-count bounds",
                       "hypothesis", "conflict", "destructive actions", "exact candidate ID/version/review-state revision",
                       "approved_for_reuse", "without per-candidate human confirmation",
                       "at most ten candidates", "no automatic publication"):
            self.assertIn(phrase, reviewer)
        extractor = (BASE / "agents/knowledge-extractor.md").read_text()
        for phrase in ("evidence_refs", "submission.evidence[].id", "same packet",
                       "stable idempotency", "enabled learning", "contribution authority",
                       "Extraction is not approval"):
            self.assertIn(phrase, extractor)

    def test_readme_version_and_remote_identity_contract(self):
        text = (BASE / "README.md").read_text()
        self.assertTrue(text.startswith("# sharpps-knowledge 0.1.6\n"))
        for phrase in ("Remote OAuth operations are attributed to the account connected",
                       "authenticated tenant/object principal", "same principal",
                       "Local/stdio UID identity and remote Entra identity",
                       "separate state, scope ownership and review consent",
                       "no per-candidate human confirmation", "prompt-level workflow instructions",
                       "not a runtime enforcement mechanism"):
            self.assertIn(phrase, text)

    def test_scenario_protocol_coverage_not_behavioral_execution(self):
        fixture = json.loads((BASE / "tests/scenarios.json").read_text())
        self.assertIn("unrun model-behavior", fixture["kind"])
        protocol = (BASE / "references/protocol.md").read_text()
        self.assertEqual(len({s["id"] for s in fixture["scenarios"]}), 48)
        for scenario in fixture["scenarios"]:
            self.assertTrue(scenario["expected_behavior"])
            for phrase in scenario["protocol_checks"]:
                self.assertIn(phrase, protocol, scenario["id"])


class SkillOnlyDistributionTests(unittest.TestCase):
    """Static SKILL-text coverage in an agents/reference-free fixture, not model runtime."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(BASE / "skills", self.root / "skills")
        self.assertFalse((self.root / "agents").exists())
        self.assertFalse((self.root / "references").exists())

    def skill(self, name):
        # Read ONLY the distributed SKILL text, never follow explanation links.
        return (self.root / "skills" / ("knowledge-" + name) / "SKILL.md").read_text()

    def require(self, text, phrases):
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_all_skills_execute_without_external_loading_prerequisites(self):
        for name in ("review", "learn", "setup", "retrieve", "status"):
            text = self.skill(name)
            self.require(text, ("self-contained", "skill-only hosts", "Claude web",
                                "optional explanation only", "not loading prerequisites",
                                "actual", "schemas", "connection identity"))
            # Detect the old mandatory protocol/role-source blockers, not optional links.
            self.assertNotRegex(text, r"(?i)read \[.*protocol[^\n]*before acting")
            self.assertNotRegex(text, r"(?i)(?:must|required to|need to) (?:read|load)[^\n]*(?:agents/|references/)")
            self.assertNotIn("use the complete compact role text from", text)
            self.assertNotIn("Missing, unreadable or incomplete role instructions block", text)

    def test_review_parent_guards_are_inline(self):
        self.require(self.skill("review"), (
            "host-established connection identity", "exact logical-to-host-tool map/schemas",
            "Never combine different connections", "Live schemas are authoritative",
            "deferred tool search", "explicit operator-selected authorized source-project IDs",
            "Collection visibility is not source-project review authority",
            "candidate-listing tools", "knowledge_get_review_policy", "knowledge_review_queue",
            "knowledge_auto_review", "supported, persisted enabled standing consent",
            "verified caller", "current source-project review authority",
            "at most ten candidates total per cycle", "max 10 across all pages/projects",
            "advertised limit is lower", "exact candidate version, review-state revision and policy revision",
            "Parent alone", "Recheck consent/authority", "revoked/expired/denied ACL",
            "stale candidate/state/policy", "Re-read queue/state", "application error payloads",
            "review_input_incomplete", "(409)", "No connector replay", "manual-review downgrade",
            "uncertain possibly committed", "Never enable consent, learning", "ACL/grants",
            "publication requires separate explicit authorization", "operator request",
            "Never use manual review to emulate standing consent", "not runtime enforcement"))

    def test_review_complete_rubric_and_honest_fallback_are_inline(self):
        self.require(self.skill("review"), (
            "verified available", "Native agents are optional", "SAME MODEL / SAME CONTEXT",
            "after extraction has finished", "weaker separation", "not a subagent or independent check",
            "not a second identity", "distinct evaluative step is mandatory",
            "Missing native role files do not block", "inline reviewer rubric",
            "untrusted data", "summary_truncated", "Unknown completeness", "missing references",
            "advertised evidence-count bounds", "no automatic approval or `evidence_supported`",
            "Unknown/skipped checks are not passing checks", "failed checks", "hypothesis",
            "preconditions, environment, specialization and limitations", "secrets", "personal information",
            "hidden reasoning", "Unsafe/conflicting claims", "destructive actions", "stop/escalate",
            "approved_for_reuse", "without per-candidate human confirmation", "contributor_reported",
            "not a blanket", "never present contributor-reported checks as independently rerun",
            "exact candidate ID/version/review-state revision", "provenance, limitations"))

    def test_learn_extraction_authorization_and_review_boundary_are_inline(self):
        self.require(self.skill("learn"), (
            "same model and context", "no external role text is needed", "Native roles are optional",
            "untrusted data", "Default to a concise reusable draft", "hypothesis",
            "preconditions, environment, specialization and limitations", "skipped/unknown checks",
            "contributor_reported", "independently rerun", "evidence_refs", "submission.evidence[].id",
            "same packet", "secrets", "hidden reasoning", "no draft", "Extraction is not approval",
            "actual contribution authority", "enabled project learning", "authorization to share",
            "not enablement or evidence-sharing consent", "defaults OFF", "explicit operator request",
            "ClientCandidateSubmission", "UTF-8", "10 candidates, 100 evidence items, 256,000",
            "stable task/submission idempotency key", "changed content needs a new key",
            "application errors", "no connector replay", "distinct evaluative review step",
            "if unavailable, leave the candidate pending", "weaker separation",
            "without per-candidate human confirmation", "exact live policy/version/state and ACL checks"))

    def test_setup_retrieval_status_keep_scope_and_error_guards_inline(self):
        setup = self.skill("setup")
        self.require(setup, ("knowledge_resolve_workspace", "workspace_namespace", "machine attestation",
                            "strict boolean", "4,096 bytes", "128 characters", "authenticated principal",
                            "learning_enabled", "scope: 'workspace'", "OFF", "older servers",
                            "no connector replay", "knowledge_workflow", "Explicit", "curated collections"))
        retrieve = self.skill("retrieve")
        self.require(retrieve, ("sort: 'recent'", "re-resolve the automatic scope", "advisory findings",
                               "never anonymous public lookup", "No namespace/scope failover", "publication"))
        status = self.skill("status")
        self.require(status, ("Status is read-only", "knowledge_list_workspaces", "opaque cursor",
                             "sole separately described write", "actual reuse", "exact selected lesson",
                             "no connector replay", "learning/policy enablement", "missing scope"))


class GlobalSearchProtocolTests(unittest.TestCase):
    """Static guard coverage only, never backend calls or model certification."""

    def test_global_opt_in_and_live_schema_guard_across_documentation(self):
        for relative in ("skills/knowledge-retrieve/SKILL.md", "skills/knowledge-setup/SKILL.md",
                         "references/protocol.md", "references/capabilities.md", "README.md"):
            with self.subTest(relative=relative):
                text = (BASE / relative).read_text()
                for phrase in ("explicit conversational request from the user to search all accessible knowledge",
                               "all_accessible", "boolean", "default false", "mutually exclusive",
                               "project_id", "collection_ids", "actual live", "pinned connection",
                               "owned", "exact READ", "current published nonprivate approved knowledge",
                               "not anonymous/public data", "enumeration", "workspace creation",
                               "no source project is selected", "unavailable", "failover"):
                    self.assertIn(phrase, text)

    def test_global_schema_guard_and_provenance_are_skill_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            shutil.copytree(BASE / "skills", fixture / "skills")
            self.assertFalse((fixture / "agents").exists())
            self.assertFalse((fixture / "references").exists())
            text = (fixture / "skills/knowledge-retrieve/SKILL.md").read_text()
            for phrase in ("check before workspace setup", "resolving its SearchRequest reference",
                           "Names, backend version labels", "strict JSON boolean `all_accessible: true`",
                           "omit `project_id` and `collection_ids` entirely", "ask which mutually exclusive mode",
                           "do not enumerate projects, scopes, namespaces or collections",
                           "No host path/namespace is needed", "no source-project workflow is required",
                           "automatically create a workspace", "same pinned connection",
                           "explicitly report all-accessible search unavailable and stop",
                           "never emulate", "unscoped legacy requests", "Denial is not older-server absence",
                           "omit `all_accessible` (default false)", "does not replace the pinned workspace scope",
                           "workflow/capability settings", "application errors/receipts",
                           "returned `collection_ids` provenance", "actual get/feedback schema",
                           "never infer source-project authority", "drop collection provenance to bypass access",
                           "Feedback is only for actual reuse", "exact selected lesson ID/version",
                           "does not change grants, collection creation/publication", "standing review"):
                self.assertIn(phrase, text)
            self.assertLess(text.index("## Explicit all-accessible"), text.index("## Ordinary scoped"))
            self.assertNotRegex(text, r"(?i)(?:must|required to) (?:read|load)[^\n]*(?:agents/|references/)")

    def test_global_mode_does_not_broaden_review_or_sharing(self):
        protocol = (BASE / "references/protocol.md").read_text()
        for phrase in ("No grants, publication, learning or consent changes",
                       "Collection-only visibility is not source-project access, contribution or review authority",
                       "Collection creation is not publication or grants",
                       "Publication requires separate authorization",
                       "SAME MODEL / SAME CONTEXT", "not a subagent, independent check",
                       "without connector replay or manual-review downgrade",
                       "never drop provenance to bypass access"):
            self.assertIn(phrase, protocol)
        scenarios = json.loads((BASE / "tests/scenarios.json").read_text())["scenarios"]
        global_cases = {s["id"] for s in scenarios if s["id"].startswith("all-accessible-")}
        self.assertEqual(global_cases, {"all-accessible-explicit", "all-accessible-not-automatic",
                                       "all-accessible-older-schema", "all-accessible-incompatible-schema",
                                       "all-accessible-no-workflow", "all-accessible-conflicting-scopes",
                                       "all-accessible-collection-provenance", "all-accessible-denied"})


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
