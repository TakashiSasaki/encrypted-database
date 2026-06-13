import json
import sys
import re

def verify_vectors(filepath):
    try:
        import jcs
    except ImportError:
        print("ERROR: jcs module not found.")
        print("This helper requires the Python 'jcs' package for baseline canonicalization.")
        print("Run: python -m pip install jcs")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        vectors = json.load(f)

    if not isinstance(vectors, list):
        print("FAILED: Top-level JSON must be a list.")
        sys.exit(1)

    for i, v in enumerate(vectors):
        if not isinstance(v, dict):
            print(f"FAILED vector at index {i}: Vector must be a JSON object.")
            sys.exit(1)

        name = v.get("name")
        description = v.get("description")
        input_data = v.get("input")
        expected_string = v.get("expected_string")
        expected_hex = v.get("expected_hex")

        # verify exact keys
        expected_keys = {"name", "description", "input", "expected_string", "expected_hex"}
        actual_keys = set(v.keys())
        if actual_keys != expected_keys:
            print(f"FAILED {name or i}: Keys mismatch. Expected {expected_keys}, got {actual_keys}")
            sys.exit(1)

        # verify types
        if not isinstance(name, str):
            print(f"FAILED at index {i}: 'name' must be a string.")
            sys.exit(1)
        if not isinstance(description, str):
            print(f"FAILED {name}: 'description' must be a string.")
            sys.exit(1)
        if not isinstance(expected_string, str):
            print(f"FAILED {name}: 'expected_string' must be a string.")
            sys.exit(1)
        if not isinstance(expected_hex, str):
            print(f"FAILED {name}: 'expected_hex' must be a string.")
            sys.exit(1)

        # verify expected_hex format
        if not re.fullmatch(r"[0-9a-f]+", expected_hex):
            print(f"FAILED {name}: 'expected_hex' must be lowercase hex.")
            sys.exit(1)

        # verify expected_hex matches expected_string
        computed_hex_from_string = expected_string.encode("utf-8").hex()
        if expected_hex != computed_hex_from_string:
            print(f"FAILED {name}: 'expected_hex' does not match utf-8 encoded 'expected_string'.")
            print(f"  computed: {computed_hex_from_string}")
            print(f"  expected: {expected_hex}")
            sys.exit(1)

        actual_bytes = jcs.canonicalize(input_data)
        actual_string = actual_bytes.decode('utf-8')
        actual_hex = actual_bytes.hex()

        if actual_string != expected_string:
            print(f"FAILED {name}: string mismatch. actual={actual_string}, expected={expected_string}")
            sys.exit(1)
        if actual_hex != expected_hex:
            print(f"FAILED {name}: hex mismatch. actual={actual_hex}, expected={expected_hex}")
            sys.exit(1)

        print(f"SUCCESS {name}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_jcs_utf16_vectors.py <path_to_vector_file.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    verify_vectors(filepath)

if __name__ == "__main__":
    main()
