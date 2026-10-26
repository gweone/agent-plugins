"""Offline tests for the retrieval-loop additions: nudge hook, retriever role, helpers, hosts."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
CHUNK = BASE / "skills/knowledge-learn/scripts/chunk_source.py"
EVAL = BASE / "skills/knowledge-retrieve/scripts/eval_retrieval.py"
GOLDEN = BASE / "skills/knowledge-retrieve/references/golden.example.json"


def run(args, data=None, cwd=None):
    return subprocess.run([sys.executable, "-I", "-B"] + [str(a) for a in args], input=data,
                          capture_output=True, timeout=10, cwd=cwd)


class NudgeHookTests(unittest.TestCase):
    def context(self, event):
        out = run([BASE / "hooks/context.py"], json.dumps({"hook_event_name": event}).encode())
        self.assertEqual(out.returncode, 0)
        return json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_prompt_nudge_is_shorter_than_session_start_and_keeps_contract(self):
        start, prompt = self.context("SessionStart"), self.context("UserPromptSubmit")
        self.assertLess(len(prompt), len(start) * 0.6)
        for phrase in ("knowledge-retrieve", "knowledge-retriever", "advisory",
                       "Accepted submission OR correction", "before final response",
                       "not consent"):
            self.assertIn(phrase, prompt)
        self.assertNotIn("PING", prompt + start)


class RetrieverRoleTests(unittest.TestCase):
    def test_retriever_is_read_only_and_parent_driven(self):
        text = (BASE / "agents/knowledge-retriever.md").read_text()
        self.assertIn("\ntools: Read\n", text)
        for phrase in ("Self-contained", "untrusted data", "Never perform MCP writes",
                       "same authenticated principal", "parent alone", "preview_only",
                       "budget_excluded_count", "semantic_coverage", "not reuse"):
            self.assertIn(phrase.lower(), text.lower(), phrase)

    def test_claude_and_cursor_retriever_share_one_body(self):
        claude = (BASE / "agents/knowledge-retriever.md").read_text()
        cursor = (BASE / "agents/cursor-knowledge-retriever.md").read_text()
        self.assertEqual(claude.split("---", 2)[2], cursor.split("---", 2)[2])
        self.assertIn("\nreadonly: true\n", cursor)
        self.assertNotIn("\ntools:", cursor)


class HostNeutralLayoutTests(unittest.TestCase):
    """Skills are the only tree every host (including skill-only hosts) receives."""

    def test_no_plugin_root_helpers_or_commands(self):
        self.assertFalse((BASE / "scripts").exists())
        self.assertFalse((BASE / "commands").exists())
        self.assertTrue(CHUNK.is_file() and EVAL.is_file() and GOLDEN.is_file())

    def test_skill_files_use_relative_paths_and_no_host_variables(self):
        for path in (BASE / "skills").rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".json"}:
                text = path.read_text()
                for variable in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_SKILL_DIR", "${"):
                    self.assertNotIn(variable, text, "%s in %s" % (variable, path))
        learn = (BASE / "skills/knowledge-learn/SKILL.md").read_text()
        retrieve = (BASE / "skills/knowledge-retrieve/SKILL.md").read_text()
        self.assertIn("scripts/chunk_source.py", learn)
        self.assertIn("scripts/eval_retrieval.py", retrieve)
        for text in (learn, retrieve):
            self.assertIn("relative to the directory containing this SKILL.md", text)
            self.assertIn("needs Python 3", text)

    def test_helpers_are_stdlib_only_and_offline(self):
        banned = {"socket", "urllib", "http", "requests", "ftplib", "smtplib", "subprocess"}
        for script in (CHUNK, EVAL):
            tree = ast.parse(script.read_text())
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    imported.add((node.module or "").split(".")[0])
            self.assertFalse(imported & banned, "%s imports %s" % (script.name, imported & banned))

    def test_helpers_run_from_a_skills_only_copy_by_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp, "skills")
            shutil.copytree(BASE / "skills", skills)  # what a skill-only host receives
            doc = Path(tmp, "doc.md")
            doc.write_text("# T\n\n## Step\n\n" + "Confirm the service responds before continuing. " * 4 + "\n")
            out = run(["scripts/chunk_source.py", doc], cwd=skills / "knowledge-learn")
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(out.stdout)["total_chunks"], 1)
            Path(tmp, "g.json").write_text(json.dumps({"cases": [{"id": "a", "query": "q", "expected": ["x"]}]}))
            Path(tmp, "r.json").write_text(json.dumps({"results": [{"id": "a", "returned": ["x@1"]}]}))
            out = run(["scripts/eval_retrieval.py", "--golden", Path(tmp, "g.json"),
                       "--results", Path(tmp, "r.json")], cwd=skills / "knowledge-retrieve")
            self.assertEqual(out.returncode, 0, out.stderr)


class ChunkerTests(unittest.TestCase):
    def chunk(self, directory, *extra):
        out = run([CHUNK, directory] + list(extra))
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_headings_provenance_secret_withholding_and_paging(self):
        setup = "# Guide\n\n## Setup\n\n" + "Install the package and verify the service answers. " * 3 + "\n"
        keys = ("\n## Keys\n\npassword: correcthorsebattery and enough extra filler text "
                "to pass the minimum chunk size.\n")
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.md").write_text(setup + keys)
            Path(tmp, "b.md").write_text(setup)  # exact duplicate of a section in a.md
            Path(tmp, "skip.bin").write_bytes(b"\x00\x01")
            result = self.chunk(tmp)
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(result["total_chunks"], 2)  # duplicate in b.md is dropped
            by_head = {tuple(c["heading_path"]): c for c in result["chunks"]}
            self.assertEqual(by_head[("Guide", "Setup")]["source"], "a.md")
            self.assertGreaterEqual(by_head[("Guide", "Setup")]["line_start"], 3)
            self.assertEqual(by_head[("Guide", "Keys")]["withheld"], "possible credential")
            self.assertIsNone(by_head[("Guide", "Keys")]["text"])
            self.assertNotIn("correcthorsebattery", json.dumps(result))
            self.assertNotIn(tmp, json.dumps(result))  # no absolute paths in output
            page = self.chunk(tmp, "--limit", "1")
            self.assertEqual(len(page["chunks"]), 1)
            self.assertEqual(page["next_offset"], 1)
            self.assertIsNone(self.chunk(tmp, "--offset", "1")["next_offset"])

    def test_missing_path_is_an_error(self):
        self.assertEqual(run([CHUNK, "/nonexistent/path"]).returncode, 2)


class EvalTests(unittest.TestCase):
    def evaluate(self, cases, results, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            g, r = Path(tmp, "g.json"), Path(tmp, "r.json")
            g.write_text(json.dumps({"cases": cases}))
            r.write_text(json.dumps({"results": results}))
            out = run([EVAL, "--golden", g, "--results", r, "--json"] + list(extra))
            return out.returncode, json.loads(out.stdout) if out.stdout else None

    def test_metrics_ignore_versions_and_score_negative_cases(self):
        code, report = self.evaluate(
            [{"id": "a", "query": "q", "expected": ["x"]}, {"id": "b", "query": "q", "expected": []},
             {"id": "c", "query": "q", "expected": ["z"]}],
            [{"id": "a", "returned": ["y@1", "x@3", "x@2"]}, {"id": "b", "returned": ["y@1"]},
             {"id": "c", "returned": []}])
        self.assertEqual(code, 0)
        self.assertEqual(report["positive_cases"], 2)
        self.assertAlmostEqual(report["hit_rate"], 0.5)
        self.assertAlmostEqual(report["mrr"], 0.25)
        self.assertAlmostEqual(report["recall_at_k"], 0.5)
        self.assertAlmostEqual(report["false_positive_rate"], 1.0)

    def test_threshold_exit_code_and_missing_results(self):
        code, report = self.evaluate([{"id": "a", "query": "q", "expected": ["x"]}], [], "--min-hit", "0.5")
        self.assertEqual(code, 1)
        self.assertEqual(report["missing_results"], ["a"])

    def test_example_golden_file_is_valid(self):
        data = json.loads(GOLDEN.read_text())
        self.assertTrue(all({"id", "query", "expected"} <= set(c) for c in data["cases"]))


if __name__ == "__main__":
    unittest.main()
