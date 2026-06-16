import sys
import json
import subprocess
import os
import unittest

class TestRunPythonNodeReleasePreflight(unittest.TestCase):
    def test_help_argument(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_preflight.py", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        self.assertIn("Distribution Release Preflight", out)
        self.assertIn("--python", out)
        self.assertIn("--node", out)
        self.assertIn("--json", out)

    @unittest.skipUnless(os.environ.get("VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS") == "1", "Gated behind VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS=1")
    def test_execution_json_mode(self):
        # Ensure json mode stdout is only json
        result2 = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_preflight.py", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result2.returncode, 0)
        try:
            json.loads(result2.stdout.strip())
        except Exception as e:
            self.fail(f"stdout is not pure JSON: {e}\n{result2.stdout}")

        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_preflight.py", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)

        self.assertEqual(data["phase"], "distribution-preflight")
        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data["credentials_required"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])

        self.assertTrue(data["python"]["ok"])
        self.assertTrue(data["python"]["smoke_test_passed"])
        self.assertTrue(data["python"]["contents_audit_passed"])

        self.assertTrue(data["node"]["ok"])
        self.assertTrue(data["node"]["smoke_test_passed"])
        self.assertTrue(data["node"]["contents_audit_passed"])

if __name__ == '__main__':
    unittest.main()
