import sys
import json
import subprocess
import os
import unittest

class TestRunPythonNodeReleaseCandidateGate(unittest.TestCase):
    def test_help_argument(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_candidate_gate.py", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        self.assertIn("First Public Release Candidate Gate", out)
        self.assertIn("--json", out)
        self.assertIn("--installed-matrix", out)
        self.assertIn("--allow-network-probes", out)

    def test_execution_json_mode(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_candidate_gate.py", "--json"],
            capture_output=True, text=True
        )
        # Even if it fails (returns 1), the output should be valid JSON.
        try:
            data = json.loads(result.stdout.strip())
        except Exception as e:
            self.fail(f"stdout is not pure JSON: {e}\n{result.stdout}")

        self.assertEqual(data["phase"], "first-public-release-candidate-gate")
        self.assertFalse(data["publishing_performed"])
        self.assertFalse(data["credentials_required"])
        self.assertFalse(data["credentials_present"])
        self.assertFalse(data["storage_format_v1_semantics_changed"])
        self.assertFalse(data["tag_created"])
        self.assertFalse(data["artifact_publication"])

        self.assertIn("python", data)
        self.assertIn("node", data)
        self.assertIn("release_notes", data)
        self.assertIn("governance", data)

        # Validates that no generated artifacts are reported
        self.assertNotIn("Generated artifacts found in tree", str(data["remaining_blockers"]))

    @unittest.skipUnless(os.environ.get("VAULT_RUN_RELEASE_CANDIDATE_GATE_TESTS") == "1", "Gated behind VAULT_RUN_RELEASE_CANDIDATE_GATE_TESTS=1")
    def test_execution_installed_matrix(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_python_node_release_candidate_gate.py", "--installed-matrix", "--json"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout.strip())

        self.assertIn("preflight", data)
        self.assertIn("installed_distribution_matrix", data["preflight"])

if __name__ == '__main__':
    unittest.main()
