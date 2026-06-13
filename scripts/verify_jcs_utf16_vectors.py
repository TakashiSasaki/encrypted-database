import json
import sys

def verify_vectors(filepath):
    try:
        import jcs
    except ImportError:
        print("jcs module not found. Run pip install jcs")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        vectors = json.load(f)

    for i, v in enumerate(vectors):
        name = v.get("name")
        input_data = v.get("input")
        expected_string = v.get("expected_string")
        expected_hex = v.get("expected_hex")

        # verify exact keys
        expected_keys = {"name", "description", "input", "expected_string", "expected_hex"}
        actual_keys = set(v.keys())
        if actual_keys != expected_keys:
            print(f"FAILED {name}: Keys mismatch. Expected {expected_keys}, got {actual_keys}")
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

if __name__ == "__main__":
    verify_vectors(sys.argv[1])
