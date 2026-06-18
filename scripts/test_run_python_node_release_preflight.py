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
        self.assertFalse(data.get("credentials_required", False))
        self.assertFalse(data.get("storage_format_v1_semantics_changed", False))
        self.assertFalse(data["credentials_required"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])

        self.assertTrue(data["python"]["ok"])
        self.assertTrue(data["python"]["smoke_test_passed"])
        self.assertTrue(data["python"]["contents_audit_passed"])

        self.assertTrue(data["node"]["ok"])
        self.assertTrue(data["node"]["smoke_test_passed"])
        self.assertTrue(data["node"]["contents_audit_passed"])

    @unittest.skipUnless(os.environ.get("VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS") == "1", "Gated behind VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS=1")
    def test_write_report(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            report_path = tf.name

        try:
            result = subprocess.run(
                [sys.executable, "scripts/run_python_node_release_preflight.py", "--write-report", report_path, "--json"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            with open(report_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["phase"], "distribution-preflight")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)


    @unittest.skipUnless(os.environ.get("VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS") == "1", "Gated behind VAULT_RUN_DISTRIBUTION_PREFLIGHT_TESTS=1")
    def test_execution_installed_matrix(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_preflight.py", "--installed-matrix", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)

        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data.get("credentials_required", False))
        self.assertFalse(data.get("storage_format_v1_semantics_changed", False))
        self.assertIn("installed_distribution_matrix", data)
        matrix = data["installed_distribution_matrix"]

        self.assertIsNotNone(matrix)
        self.assertEqual(matrix["mode"], "installed-distribution-matrix")
        self.assertEqual(matrix["pairs_total"], 4)
        self.assertEqual(matrix["pairs_passed"], 4)

        self.assertEqual(matrix.get("baseline_public_certification"), "previously-certified")
        self.assertTrue(matrix.get("installed_distribution_preflight_passed"))
        self.assertFalse(matrix.get("publishing_certification"))
        self.assertFalse(matrix.get("artifact_publication"))

        for record in matrix["records"]:
            self.assertEqual(record["status"], "passed")
            self.assertIsNotNone(record["provenance"]["writer"])
            self.assertIsNotNone(record["provenance"]["reader"])
            # Provenance must be outside repo tree
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if record["pair"].startswith("python"):
                self.assertTrue(os.path.isabs(record["provenance"]["writer"]))
                self.assertFalse(record["provenance"]["writer"].startswith(repo_root + os.sep))
                self.assertIn("site-packages", record["provenance"]["writer"])
            if record["pair"].endswith("node"):
                self.assertTrue(os.path.isabs(record["provenance"]["reader"]))
                self.assertFalse(record["provenance"]["reader"].startswith(repo_root + os.sep))
                self.assertIn("node_modules", record["provenance"]["reader"])


if __name__ == '__main__':
    unittest.main()
