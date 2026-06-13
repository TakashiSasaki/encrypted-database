import unittest
import tempfile
import os
import json
import subprocess
import sys

class TestGenerateJcsPositiveLoaderFixtures(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.script_path = os.path.join(os.path.dirname(__file__), 'generate_jcs_positive_loader_fixtures.py')
        self.c_out = os.path.join(self.temp_dir.name, 'out.h')
        self.cpp_out = os.path.join(self.temp_dir.name, 'out.hpp')

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_script(self, input_data):
        input_file = os.path.join(self.temp_dir.name, 'input.json')
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(input_data, f)

        result = subprocess.run(
            [sys.executable, self.script_path, '--c-out', self.c_out, '--cpp-out', self.cpp_out, input_file],
            capture_output=True, text=True
        )
        return result

    def test_valid_minimal_vector(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": {},
            "expected_string": "{}",
            "expected_hex": "7b7d"
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("included: 1, excluded: 0", res.stdout)
        self.assertTrue(os.path.exists(self.c_out))
        self.assertTrue(os.path.exists(self.cpp_out))

    def test_unknown_metadata_excluded(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": {},
            "expected_string": "{}",
            "expected_hex": "7b7d",
            "unknown_field": "test"
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("unknown or unsupported fields: unknown_field", res.stdout)

    def test_missing_input_excluded(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "expected_string": "{}",
            "expected_hex": "7b7d"
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("missing required fields: input", res.stdout)

    def test_wrong_metadata_type_excluded(self):
        data = [{
            "name": 123,
            "description": "desc",
            "input": {},
            "expected_string": "{}",
            "expected_hex": "7b7d"
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: 123", res.stdout)
        self.assertIn("'name' must be a string", res.stdout)

    def test_float_input_excluded(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": {"val": 1.5},
            "expected_string": "...",
            "expected_hex": "..."
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("float unsupported", res.stdout)

    def test_unsafe_integer_input_excluded(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": {"val": 9007199254740992},
            "expected_string": "...",
            "expected_hex": "..."
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("unsafe integer", res.stdout)

    def test_embedded_nul_excluded(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": {"val": "a\u0000b"},
            "expected_string": "...",
            "expected_hex": "..."
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("embedded NUL", res.stdout)

    def test_rejection_metadata_rejected(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input_raw_json": "{}",
            "expected_error": "err",
            "future_only": True
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("excluded: test1", res.stdout)
        self.assertIn("unknown or unsupported fields", res.stdout)

    def test_top_level_null_accepted(self):
        data = [{
            "name": "test1",
            "description": "desc",
            "input": None,
            "expected_string": "null",
            "expected_hex": "6e756c6c"
        }]
        res = self.run_script(data)
        self.assertEqual(res.returncode, 0)
        self.assertIn("included: 1, excluded: 0", res.stdout)

if __name__ == '__main__':
    unittest.main()
