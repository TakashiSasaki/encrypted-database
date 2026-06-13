import argparse
import json
import os
import subprocess
import sys
import tempfile

# Discovery/Reporting Script and Matrix Executor
# This script reports on the matrix execution status and executes test pairs.

LANGUAGES = {
    "python": {"public_read": "known-api-unverified", "public_write": "known-api-unverified", "scaffold_only": False, "wrapper": "python/tests/compatibility_wrapper.py"},
    "nodejs": {"public_read": "known-api-unverified", "public_write": "known-api-unverified", "scaffold_only": False, "wrapper": "nodejs/test/compatibility_wrapper.js"},
    "go": {"public_read": "not-implemented", "public_write": "not-implemented", "scaffold_only": True},
    "rust": {"public_read": "not-implemented", "public_write": "not-implemented", "scaffold_only": True},
    "zig": {"public_read": "not-implemented", "public_write": "not-implemented", "scaffold_only": True},
    "c": {"public_read": "not-implemented", "public_write": "not-implemented", "scaffold_only": True},
    "cpp": {"public_read": "not-implemented", "public_write": "not-implemented", "scaffold_only": True},
}

TEST_PAYLOADS = [
    {},
    {"message": "hello world"},
    {"message": "こんにちは"},
    {"nested": {"array": [None, True, 42, "text"]}}
]
SCHEMA_UUID = "00000000-0000-4000-8000-000000000000"
CONTENT_TYPE = "application/json"
PASSPHRASE = "test_passphrase_123"

def _get_wrapper_cmd(lang, op, db_path, object_uuid=None):
    wrapper_path = LANGUAGES[lang].get("wrapper")
    if not wrapper_path or not os.path.exists(wrapper_path):
        return None

    if lang == "python":
        cmd = ["python", wrapper_path, op, "--db", db_path, "--schema", SCHEMA_UUID, "--content-type", CONTENT_TYPE]
    elif lang == "nodejs":
        cmd = ["node", wrapper_path, op, "--db", db_path, "--schema", SCHEMA_UUID, "--content-type", CONTENT_TYPE]
    else:
        return None

    if object_uuid:
        cmd.extend(["--object-uuid", object_uuid])

    return cmd

def _run_wrapper(cmd, payload=None):
    env = os.environ.copy()
    env["VAULT_PASSPHRASE"] = PASSPHRASE
    input_data = json.dumps(payload) if payload is not None else None

    try:
        proc = subprocess.run(cmd, input=input_data, capture_output=True, env=env, text=True)
    except Exception as e:
        return False, str(e), None

    if proc.returncode != 0:
        return False, f"Process exited with {proc.returncode}. stderr: {proc.stderr}", None

    try:
        out = json.loads(proc.stdout)
        if out.get("ok"):
            return True, None, out
        else:
            return False, out.get("error", "Unknown error"), out
    except json.JSONDecodeError:
        return False, f"Failed to parse stdout as JSON: {proc.stdout}", None

def execute_pair(writer, reader):
    if LANGUAGES[writer]["scaffold_only"]:
        return "skipped", "writer is scaffold-only; lacks stable public API", None
    if LANGUAGES[reader]["scaffold_only"]:
        return "skipped", "reader is scaffold-only; lacks stable public API", None

    w_cmd = _get_wrapper_cmd(writer, "write", "dummy")
    r_cmd = _get_wrapper_cmd(reader, "read", "dummy", "dummy")

    if not w_cmd or not r_cmd:
        return "skipped", "matrix_status: not-yet-runnable, missing wrapper command/test fixture contract", None

    # Do the actual test for each payload
    for payload in TEST_PAYLOADS:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Write
            cmd_w = _get_wrapper_cmd(writer, "write", db_path)
            w_ok, w_err, w_out = _run_wrapper(cmd_w, payload)
            if not w_ok:
                return "failed", f"Write failed: {w_err}", None

            object_uuid = w_out.get("object_uuid")
            if not object_uuid:
                return "failed", "Write did not return object_uuid", None

            # Read
            cmd_r = _get_wrapper_cmd(reader, "read", db_path, object_uuid)
            r_ok, r_err, r_out = _run_wrapper(cmd_r)
            if not r_ok:
                return "failed", f"Read failed: {r_err}", None

            retrieved = r_out.get("payload")
            if retrieved != payload:
                return "failed", f"Payload mismatch. Expected {payload}, got {retrieved}", None

    return "passed", "Successfully executed cross-language tests", None

def main():
    parser = argparse.ArgumentParser(description="Cross-Language Read/Write Compatibility Matrix")
    parser.add_argument("--list", action="store_true", help="List matrix discovery")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--execute", action="store_true", help="Execute runnable pairs")
    parser.add_argument("--pair", help="Execute a specific pair like 'python:nodejs'")

    args = parser.parse_args()

    # Default to list if nothing is specified
    if not (args.list or args.execute or args.pair):
        args.list = True

    results = []

    if args.pair:
        w, r = args.pair.split(":")
        if w not in LANGUAGES or r not in LANGUAGES:
            print(f"Invalid pair {args.pair}")
            sys.exit(1)
        pairs_to_run = [(w, r)]
        args.execute = True
    else:
        pairs_to_run = [(w, r) for w in LANGUAGES for r in LANGUAGES]

    all_passed = True
    for w, r in pairs_to_run:
        if args.execute:
            status, reason, evidence = execute_pair(w, r)
            if status == "failed":
                all_passed = False
        else:
            if LANGUAGES[w]["scaffold_only"]:
                status = "skipped"
                reason = "writer is scaffold-only; lacks stable public API"
            elif LANGUAGES[r]["scaffold_only"]:
                status = "skipped"
                reason = "reader is scaffold-only; lacks stable public API"
            else:
                if _get_wrapper_cmd(w, "write", "dummy") and _get_wrapper_cmd(r, "read", "dummy", "dummy"):
                    status = "candidate"
                    reason = "Wrapper commands exist, runnable with --execute"
                else:
                    status = "skipped"
                    reason = "matrix_status: not-yet-runnable, missing wrapper command/test fixture contract"

        results.append({
            "writer": w,
            "reader": r,
            "status": status,
            "reason": reason,
            "evidence": None
        })

    if args.json:
        output = {
            "mode": "execute" if args.execute else "discovery",
            "language_inventory": LANGUAGES,
            "pair_matrix": results
        }
        print(json.dumps(output, indent=2))
        sys.exit(0 if all_passed else 1)

    # Plain text output
    print(f"Cross-Language Read/Write Compatibility Matrix ({'Execute' if args.execute else 'Discovery'})")
    print("=" * 60)
    for res in results:
        print(f"{res['writer']:10} (write) -> {res['reader']:10} (read) : {res['status']} ({res['reason']})")

    print("\nSummary:")
    if args.execute:
        passed = [r for r in results if r['status'] == 'passed']
        if passed:
            print(f"Matrix execution integrated. {len(passed)} pairs passed.")
        else:
            print("No active pairs are currently runnable or passed.")
    else:
        print("Python and Node.js are candidate baseline participants.")
        print("Use --execute to run the compatibility matrix.")
    print("No unsupported or skipped pairs are falsely claimed as passed.")

    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
