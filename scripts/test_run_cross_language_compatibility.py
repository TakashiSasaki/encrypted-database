import json
import subprocess
import unittest
import os

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

    @unittest.skipUnless(os.environ.get("VAULT_RUN_COMPAT_EXECUTION_TESTS") == "1", "Execution tests gated behind VAULT_RUN_COMPAT_EXECUTION_TESTS=1")
    def test_execution_mode(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--execute"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        self.assertIn("Matrix execution integrated. 4 pairs passed.", out)
        self.assertIn("python     (write) -> python     (read) : passed", out)
        self.assertIn("python     (write) -> nodejs     (read) : passed", out)
        self.assertIn("nodejs     (write) -> python     (read) : passed", out)
        self.assertIn("nodejs     (write) -> nodejs     (read) : passed", out)

    @unittest.skipUnless(os.environ.get("VAULT_RUN_COMPAT_EXECUTION_TESTS") == "1", "Execution tests gated behind VAULT_RUN_COMPAT_EXECUTION_TESTS=1")
    def test_execution_mode_json(self):
        result = subprocess.run(
            ["python", "scripts/run_cross_language_compatibility.py", "--execute", "--json"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["mode"], "execute")

        passed_pairs = [p for p in data["pair_matrix"] if p["status"] == "passed"]
        self.assertEqual(len(passed_pairs), 4)

if __name__ == '__main__':
    unittest.main()
