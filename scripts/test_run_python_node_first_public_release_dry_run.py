import sys
import json
import subprocess
import os
import tempfile
import unittest

class TestRunPythonNodeFirstPublicReleaseDryRun(unittest.TestCase):
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_first_public_release_dry_run.py", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("First Public Release Dry Run Aggregator", result.stdout)
        self.assertIn("--json", result.stdout)

    def test_default_informational_mode(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_first_public_release_dry_run.py", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)

        # Verify stderr doesn't contaminate json stdout
        try:
            data = json.loads(result.stdout)
        except Exception as e:
            self.fail(f"stdout is not pure JSON: {e}\n{result.stdout}")

        self.assertEqual(data["phase"], "first-public-release-dry-run")
        self.assertTrue(data["preflight_checked"])
        self.assertTrue(data["release_candidate_gate_checked"])
        self.assertTrue(data["publication_readiness_gate_checked"])

        # Explicit bounds
        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data["credentials_present"])
        self.assertFalse(data["tag_created"])
        self.assertFalse(data["tag_pushed"])
        self.assertFalse(data["artifact_publication"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])

        self.assertFalse(data["publication_ready"])
        self.assertFalse(data["installed_matrix_checked"])

    def test_require_publication_ready_fails(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_first_public_release_dry_run.py", "--require-publication-ready", "--json"],
            capture_output=True, text=True
        )
        # Should fail as manual decisions remain pending
        self.assertEqual(result.returncode, 1)

    def test_include_installed_matrix(self):
        # We assume installed matrix tests pass when run normally. This ensures we are properly parsing the passed status.
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_first_public_release_dry_run.py", "--include-installed-matrix", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data["installed_matrix_checked"])
        self.assertTrue(data["installed_matrix_passed"])

    def test_write_report(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            report_path = tf.name

        try:
            result = subprocess.run(
                [sys.executable, "scripts/run_python_node_first_public_release_dry_run.py", "--write-report", report_path, "--json"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            with open(report_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["phase"], "first-public-release-dry-run")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

if __name__ == '__main__':
    unittest.main()
