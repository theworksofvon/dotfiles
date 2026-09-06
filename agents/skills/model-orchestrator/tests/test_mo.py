import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "mo.py"


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args], text=True, capture_output=True)


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        (self.root / ".orchestrator").mkdir()
        (self.root / ".orchestrator" / "config.toml").write_text('''default_profile = "mixed"
[profiles.mixed]
planner = "fake-strong"
implementer = "fake-cheap"
[profiles.claude]
planner = "fake-strong"
[models]
fake-strong = { model = "strong-1", provider = "echoer" }
fake-cheap = { model = "cheap-1", provider = "echoer" }
[providers]
echoer = "echo '{\\"usage\\":{\\"input_tokens\\":1,\\"output_tokens\\":1}}'; echo {model} {stage} >&2"
[pricing.codex-medium]
input_per_1m = 1.0
output_per_1m = 2.0
''')

    def tearDown(self): self.tmp.cleanup()

    def test_json_exact_and_redaction(self):
        p = 'echo \'{"request_id":"r1","usage":{"input_tokens":10,"output_tokens":5},"cost_usd":0.42,"api_key=secret":"x"}\''
        r = run(self.root, "run-stage", "--task-id", "TASK-123", "--stage", "implement", "--provider", "claude", "--model", "codex-medium", "--command", p)
        self.assertEqual(r.returncode, 0); row = json.loads(r.stdout); self.assertEqual(row["cost_status"], "exact")
        raw = (self.root / row["raw_output_path"]).read_text(); self.assertNotIn("secret", raw)

    def test_jsonl_estimate_missing_cost_and_report(self):
        p = 'printf \'{"usage":{"input_tokens":100,"output_tokens":50}}\\n{"usage":{"input_tokens":20,"output_tokens":10}}\\n\''
        r = run(self.root, "run-stage", "--task-id", "TASK-123", "--stage", "review", "--provider", "codex", "--model", "codex-medium", "--command", p)
        row = json.loads(r.stdout); self.assertEqual(row["total_tokens"], 180); self.assertEqual(row["cost_status"], "estimated")
        report = json.loads(run(self.root, "report", "TASK-123").stdout); self.assertEqual(report["total_tokens"], 180)

    def test_duplicate_stream_events_are_counted_once(self):
        line = '{"event_id":"e1","usage":{"input_tokens":4,"output_tokens":6}}'
        p = "printf '%s\\n%s\\n' '" + line + "' '" + line + "'"
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "stream", "--provider", "claude", "--command", p)
        self.assertEqual(json.loads(r.stdout)["total_tokens"], 10)

    def test_missing_usage_malformed_and_failed_timeout(self):
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "x", "--provider", "cursor", "--command", "echo not-json")
        self.assertEqual(json.loads(r.stdout)["cost_status"], "unavailable")
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "bad", "--provider", "x", "--command", "exit 7")
        self.assertEqual(r.returncode, 7); self.assertFalse(json.loads(r.stdout)["success"])
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "slow", "--provider", "x", "--command", "sleep 1", "--timeout", "0.01")
        self.assertEqual(r.returncode, 124)

    def test_claude_print_json_shape_is_exact(self):
        # Shape of `claude -p --output-format json` as of Claude Code 2.x.
        p = 'echo \'{"type":"result","total_cost_usd":0.0237,"duration_api_ms":2273,"session_id":"s1","usage":{"input_tokens":3,"output_tokens":5,"cache_read_input_tokens":900}}\''
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "plan", "--provider", "claude", "--command", p)
        row = json.loads(r.stdout); self.assertEqual(row["cost_status"], "exact"); self.assertEqual(row["provider_cost_usd"], 0.0237)
        self.assertEqual(row["api_duration_seconds"], 2.273); self.assertEqual(row["session_id"], "s1"); self.assertEqual(row["cache_read_tokens"], 900)

    def test_placeholders_are_shell_quoted(self):
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "s", "--provider", "x", "--run-id", "run with space", "--command", "test -d {run_dir} && echo '{}'")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_role_resolves_through_default_and_named_profile(self):
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "implement", "--role", "implementer")
        row = json.loads(r.stdout); self.assertEqual((row["profile"], row["provider"], row["resolved_model"]), ("mixed", "echoer", "cheap-1"))
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "plan", "--profile", "claude", "--role", "planner")
        self.assertEqual(json.loads(r.stdout)["resolved_model"], "strong-1")
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "review", "--profile", "claude", "--role", "reviewer")
        self.assertEqual(r.returncode, 2); self.assertIn("no role 'reviewer'", r.stderr)
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "x", "--model", "unknown-alias")
        self.assertEqual(r.returncode, 2); self.assertIn("No provider", r.stderr)
        table = json.loads(run(self.root, "profiles").stdout)
        self.assertEqual(table["profiles"]["mixed"]["implementer"], {"alias": "fake-cheap", "model": "cheap-1", "provider": "echoer"})

    def test_opencode_events_and_last_message(self):
        # Shape of `opencode run --format json` as of opencode 1.18.
        lines = [
            '{"type":"step_start","sessionID":"ses_1","part":{"type":"step-start"}}',
            '{"type":"text","sessionID":"ses_1","part":{"type":"text","text":"ok"}}',
            '{"type":"step_finish","sessionID":"ses_1","part":{"type":"step-finish","tokens":{"total":9128,"input":9093,"output":4,"reasoning":31,"cache":{"write":0,"read":0}},"cost":0.00069}}',
        ]
        p = "printf '%s\\n' " + " ".join("'" + l + "'" for l in lines)
        r = run(self.root, "run-stage", "--task-id", "T", "--stage", "implement", "--provider", "opencode", "--command", p)
        row = json.loads(r.stdout); self.assertEqual(row["cost_status"], "exact"); self.assertEqual(row["total_tokens"], 9128)
        self.assertEqual(row["reasoning_tokens"], 31); self.assertEqual(row["session_id"], "ses_1")
        self.assertEqual((self.root / row["message_path"]).read_text(), "ok")

    def test_claude_result_becomes_last_message(self):
        p = 'echo \'{"type":"result","result":"the plan","total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1}}\''
        row = json.loads(run(self.root, "run-stage", "--task-id", "T", "--stage", "plan", "--provider", "claude", "--command", p).stdout)
        self.assertEqual((self.root / row["message_path"]).read_text(), "the plan")

    def test_resume_and_exports_dashboard(self):
        p = 'echo \'{"usage":{"input_tokens":1,"output_tokens":1},"cost":0.1}\''
        args = ("run-stage", "--task-id", "T", "--stage", "one", "--provider", "x", "--model", "m", "--run-id", "run1", "--command", p)
        self.assertEqual(run(self.root, *args).returncode, 0); self.assertEqual(run(self.root, *args, "--resume").returncode, 0)
        self.assertEqual(run(self.root, "export", "--format", "csv").returncode, 0)
        d = run(self.root, "dashboard", "--write-only"); self.assertEqual(d.returncode, 0); self.assertIn("dashboard.html", d.stdout)
        self.assertIn('"stages": 1', (self.root / ".orchestrator" / "dashboard.html").read_text())


if __name__ == "__main__": unittest.main()
