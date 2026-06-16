import sys
import json
import subprocess
import os
import tempfile
import unittest

class TestRunPythonNodePublicationReadinessGate(unittest.TestCase):
    def test_default_informational_mode(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_publication_readiness_gate.py", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)

        self.assertEqual(data["phase"], "first-public-release-publication-readiness-gate")
        self.assertFalse(data["publication_authorized"])
        self.assertFalse(data["publication_ready"])
        self.assertFalse(data["credentials_configured"])
        self.assertFalse(data["trusted_publishing_configured"])
        self.assertFalse(data["tag_created"])
        self.assertFalse(data["tag_pushed"])
        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])
        self.assertTrue(len(data["remaining_blockers"]) > 0)

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
            self.assertEqual(data["phase"], "first-public-release-publication-readiness-gate")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

if __name__ == '__main__':
    unittest.main()
