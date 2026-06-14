import json
import subprocess
import os
import unittest

class TestRunCrossLanguageCompatibility(unittest.TestCase):
    def test_discovery_mode_plain(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--list"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        self.assertIn("Cross-Language Read/Write Compatibility Matrix (Discovery)", out)
        self.assertIn("Python and Node.js are candidate baseline participants", out)
        self.assertIn("go         (write) -> go         (read) : skipped (writer is scaffold-only", out)

    def test_discovery_mode_json(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--list", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)

        self.assertEqual(data["mode"], "discovery")
        self.assertIn("python", data["language_inventory"])
        self.assertFalse(data["language_inventory"]["python"]["scaffold_only"])
        self.assertTrue(data["language_inventory"]["go"]["scaffold_only"])

        pairs = data["pair_matrix"]
        self.assertTrue(any(p["writer"] == "python" and p["reader"] == "nodejs" and p["status"] == "candidate" for p in pairs))
        self.assertTrue(any(p["writer"] == "go" and p["status"] == "skipped" for p in pairs))

    @unittest.skipUnless(os.environ.get("VAULT_RUN_COMPAT_EXECUTION_TESTS") == "1", "Gated behind VAULT_RUN_COMPAT_EXECUTION_TESTS=1")
    def test_execution_mode(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--execute"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        self.assertIn("4 pairs passed via test-only compatibility wrappers.", out)
        self.assertIn("python     (write) -> python     (read) : test-wrapper-passed", out)
        self.assertIn("python     (write) -> nodejs     (read) : test-wrapper-passed", out)
        self.assertIn("nodejs     (write) -> python     (read) : test-wrapper-passed", out)
        self.assertIn("nodejs     (write) -> nodejs     (read) : test-wrapper-passed", out)

    @unittest.skipUnless(os.environ.get("VAULT_RUN_COMPAT_EXECUTION_TESTS") == "1", "Gated behind VAULT_RUN_COMPAT_EXECUTION_TESTS=1")
    def test_execution_mode_json(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--execute", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "execute")

        passed_pairs = [p for p in data["pair_matrix"] if p["status"] == "test-wrapper-passed"]
        self.assertEqual(len(passed_pairs), 4)
        for pair in passed_pairs:
            self.assertIsNotNone(pair["evidence"])
            self.assertEqual(pair["evidence"]["mode"], "public-entrypoint-test-wrapper")
            self.assertTrue(pair["evidence"]["public_entrypoint"])
            self.assertEqual(pair["evidence"]["operations"], ["write", "read", "update", "delete", "not_found_after_delete"])
            self.assertFalse(pair["evidence"]["public_quality_certification"])
            self.assertEqual(pair["evidence"]["database"], "temporary-file")
            self.assertEqual(pair["evidence"]["artifact_policy"], "not committed")

if __name__ == '__main__':
    unittest.main()
