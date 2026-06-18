import sys
import json
import subprocess
import os
import tempfile
import unittest

class TestRunPythonNodePublicationReadinessGate(unittest.TestCase):
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("First Public Release Execution Approval Readiness Gate", result.stdout)

    def test_default_informational_mode(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)

        self.assertEqual(data["phase"], "first-public-release-execution-approval-readiness")
        self.assertTrue(data["decision_record_found"])
        self.assertFalse(data["publication_authorized"])
        self.assertFalse(data["publication_ready"])
        self.assertFalse(data["credentials_configured"])
        self.assertFalse(data["credentials_required"])
        self.assertFalse(data["credentials_present"])
        self.assertFalse(data["trusted_publishing_configured"])
        self.assertFalse(data["tag_created"])
        self.assertFalse(data["tag_pushed"])
        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data["artifact_publication"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])
        self.assertTrue(len(data["remaining_blockers"]) > 0)
        self.assertTrue(data["decision_record_placeholders_remaining"] > 0)

    def test_require_publication_ready_fails(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--require-publication-ready", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)

    def test_write_report(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            report_path = tf.name

        try:
            result = subprocess.run(
                [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--write-report", report_path, "--json"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            with open(report_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["phase"], "first-public-release-execution-approval-readiness")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

    def test_missing_decision_record(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--decision-record", "non_existent_file.md", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["decision_record_found"])
        self.assertIn("Decision record not found", data["remaining_blockers"][0])

    def test_approved_decision_record(self):
        # We need to get the real HEAD sha to avoid the blocker
        head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()

        # Create a mock approved decision record file that doesn't trigger any blockers
        mock_content = f"""# Python/Node.js First Public Release Decision Record
- Status: APPROVED
- Publication Authorized: true
- Publishing Performed: false
- Credentials Present: false
- Trusted Publishing Setup Configured: false
- Release Tag Created: false
- Release Tag Pushed: false
- Storage Format V1 Semantics Changed: false
- PyPI Project/Account Decision: Done
- npm Package/Scope/Account Decision: Done
- Trusted Publishing/Token Decision: Done
- Release Manager Approval: Alice
- Candidate Commit SHA: {head_sha}
- Gate Result: PASS

## Target Packages
- **Python:** `encrypted_storage` (Version: 0.1.0)
- **Node.js:** `encrypted-storage` (Version: 0.1.0)
"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as tf:
            tf.write(mock_content)
            record_path = tf.name

        try:
            result = subprocess.run(
                [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--decision-record", record_path, "--json"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertTrue(data["decision_record_found"])
            self.assertEqual(data["decision_record_placeholders_remaining"], 0)
            # The mocked decision record removed all human blockers, so it's fully ready assuming RC is ready.
            # RC Gate may be false or true depending on the env, so we just check blockers.
            self.assertNotIn("Decision record status is PENDING.", data["remaining_blockers"])
            self.assertNotIn("Manual approval decision is pending.", data["remaining_blockers"])
            # In our mock test, it will probably complain about Release candidate gate is not ready if it isn't, but that's fine.
            if data["release_candidate_freeze_ready"]:
                self.assertTrue(data["publication_ready"])
        finally:
            if os.path.exists(record_path):
                os.remove(record_path)

if __name__ == '__main__':
    unittest.main()
