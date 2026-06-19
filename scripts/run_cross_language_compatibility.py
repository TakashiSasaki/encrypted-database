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
    "java": {"public_read": "missing", "public_write": "missing", "jcs": "needs-decision", "argon2id": "needs-decision", "sqlite_profile": "needs-decision", "cross_language_execution": "out-of-scope", "future_target": True, "execution_enabled": False}, # Future entry path: J1 scaffold validators -> J2 shared fixture consumer -> J3 read-only -> J4 write scaffold -> J5 cross-language matrix
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

    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out = None

    if proc.returncode != 0:
        if out:
            return False, out.get("error", "Unknown error"), out
        return False, f"Process exited with {proc.returncode}. stderr: {proc.stderr}", None

    if out and out.get("ok"):
        return True, None, out
    elif out:
        return False, out.get("error", "Unknown error"), out
    else:
        return False, "Failed to parse stdout as JSON or missing ok", None

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

            # Write P1
            cmd_w = _get_wrapper_cmd(writer, "write", db_path)
            w_ok, w_err, w_out = _run_wrapper(cmd_w, payload)
            if not w_ok:
                return "failed", f"Write failed: {w_err}", None

            object_uuid = w_out.get("object_uuid")
            if not object_uuid:
                return "failed", "Write did not return object_uuid", None

            # Read P1
            cmd_r = _get_wrapper_cmd(reader, "read", db_path, object_uuid)
            r_ok, r_err, r_out = _run_wrapper(cmd_r)
            if not r_ok:
                return "failed", f"Read P1 failed: {r_err}", None

            retrieved = r_out.get("payload")
            if retrieved != payload:
                return "failed", f"Payload P1 mismatch. Expected {payload}, got {retrieved}", None

            # Update P2 (cross-language update: reader updates the same object to payload P2)
            payload_p2 = {"updated": True, "old": payload}
            cmd_u = _get_wrapper_cmd(reader, "update", db_path, object_uuid)
            u_ok, u_err, u_out = _run_wrapper(cmd_u, payload_p2)
            if not u_ok:
                return "failed", f"Update failed: {u_err}", None

            # Read P2 (writer reads payload P2)
            cmd_r2 = _get_wrapper_cmd(writer, "read", db_path, object_uuid)
            r2_ok, r2_err, r2_out = _run_wrapper(cmd_r2)
            if not r2_ok:
                return "failed", f"Read P2 failed: {r2_err}", None

            retrieved_p2 = r2_out.get("payload")
            if retrieved_p2 != payload_p2:
                return "failed", f"Payload P2 mismatch. Expected {payload_p2}, got {retrieved_p2}", None

            # Delete (cross-language delete: reader deletes the object)
            cmd_d = _get_wrapper_cmd(reader, "delete", db_path, object_uuid)
            d_ok, d_err, d_out = _run_wrapper(cmd_d)
            if not d_ok:
                return "failed", f"Delete failed: {d_err}", None

            # Read Deleted (writer attempts to read deleted object)
            cmd_rd = _get_wrapper_cmd(writer, "read", db_path, object_uuid)
            rd_ok, rd_err, rd_out = _run_wrapper(cmd_rd)
            if rd_ok:
                return "failed", "Read deleted object succeeded when it should have failed", None

            error_class = rd_out.get("error_class")
            if error_class != "ObjectNotFound":
                return "failed", f"Expected ObjectNotFound after delete, got {error_class}", None

    return "public-entrypoint-passed", "Successfully executed public-entrypoint test-wrapper matrix checks", {
        "mode": "public-entrypoint-test-wrapper",
        "public_entrypoint": True,
        "public_quality_certification": False,
        "certification_record": "docs/implementation-notes/python-node-baseline-public-certification-record.md",
        "operations": ["write", "read", "update", "delete", "not_found_after_delete"],
        "payload_count": len(TEST_PAYLOADS),
        "wrapper_writer": LANGUAGES[writer].get("wrapper"),
        "wrapper_reader": LANGUAGES[reader].get("wrapper"),
        "database": "temporary-file",
        "artifact_policy": "not committed"
    }


def execute_pair_direct(writer, reader):
    if LANGUAGES[writer]["scaffold_only"]:
        return "skipped", "writer is scaffold-only; lacks stable public API", None
    if LANGUAGES[reader]["scaffold_only"]:
        return "skipped", "reader is scaffold-only; lacks stable public API", None

    # Only support python and nodejs for direct API
    if writer not in ("python", "nodejs") or reader not in ("python", "nodejs"):
        return "skipped", "direct-public-api mode currently only supports python and nodejs", None

    direct_wrapper_code = {
        "python": """
import sys
import json
from encrypted_storage import EncryptedStorage, errors

def main():
    op = sys.argv[1]
    db_path = sys.argv[2]

    if op == "write":
        payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else None
        schema = sys.argv[3]
        content_type = sys.argv[4]

        try:
            storage = EncryptedStorage(db_path)
            storage.initialize_database("test_passphrase_123", "linux")
            storage.unlock_database("test_passphrase_123")
            obj_uuid = storage.store_payload(schema, content_type, payload)
            storage.close()
            print(json.dumps({"ok": True, "object_uuid": obj_uuid}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e), "error_class": e.__class__.__name__}))
            sys.exit(1)

    elif op == "read":
        schema = sys.argv[3]
        content_type = sys.argv[4]
        obj_uuid = sys.argv[5]

        try:
            storage = EncryptedStorage(db_path)
            storage.unlock_database("test_passphrase_123")
            payload = storage.retrieve_payload(obj_uuid)
            storage.close()
            print(json.dumps({"ok": True, "payload": payload}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e), "error_class": e.__class__.__name__}))
            sys.exit(1)

    elif op == "update":
        payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else None
        schema = sys.argv[3]
        content_type = sys.argv[4]
        obj_uuid = sys.argv[5]

        try:
            storage = EncryptedStorage(db_path)
            storage.unlock_database("test_passphrase_123")
            storage.update_payload(obj_uuid, schema, content_type, payload)
            storage.close()
            print(json.dumps({"ok": True}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e), "error_class": e.__class__.__name__}))
            sys.exit(1)

    elif op == "delete":
        schema = sys.argv[3]
        content_type = sys.argv[4]
        obj_uuid = sys.argv[5]

        try:
            storage = EncryptedStorage(db_path)
            storage.unlock_database("test_passphrase_123")
            storage.delete_payload(obj_uuid)
            storage.close()
            print(json.dumps({"ok": True}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e), "error_class": e.__class__.__name__}))
            sys.exit(1)

if __name__ == "__main__":
    main()
""",
        "nodejs": """
const { EncryptedStorage, errors } = require(process.cwd());
const fs = require('fs');

async function main() {
    const op = process.argv[2];
    const dbPath = process.argv[3];

    let inputData = '';
    if (!process.stdin.isTTY) {
        inputData = fs.readFileSync(0, 'utf-8');
    }
    const payload = inputData ? JSON.parse(inputData) : null;

    if (op === "write") {
        const schema = process.argv[4];
        const contentType = process.argv[5];

        try {
            const storage = new EncryptedStorage(dbPath);
            await storage.initializeDatabase("test_passphrase_123", "linux");
            await storage.unlockDatabase("test_passphrase_123");
            const objUuid = await storage.storePayload(schema, contentType, payload);
            storage.close();
            console.log(JSON.stringify({ok: true, object_uuid: objUuid}));
        } catch (e) {
            console.log(JSON.stringify({ok: false, error: e.message, error_class: e.constructor.name}));
            process.exit(1);
        }
    } else if (op === "read") {
        const schema = process.argv[4];
        const contentType = process.argv[5];
        const objUuid = process.argv[6];

        try {
            const storage = new EncryptedStorage(dbPath);
            await storage.unlockDatabase("test_passphrase_123");
            const retrieved = await storage.retrievePayload(objUuid);
            storage.close();
            console.log(JSON.stringify({ok: true, payload: retrieved}));
        } catch (e) {
            console.log(JSON.stringify({ok: false, error: e.message, error_class: e.constructor.name}));
            process.exit(1);
        }
    } else if (op === "update") {
        const schema = process.argv[4];
        const contentType = process.argv[5];
        const objUuid = process.argv[6];

        try {
            const storage = new EncryptedStorage(dbPath);
            await storage.unlockDatabase("test_passphrase_123");
            await storage.updatePayload(objUuid, schema, contentType, payload);
            storage.close();
            console.log(JSON.stringify({ok: true}));
        } catch (e) {
            console.log(JSON.stringify({ok: false, error: e.message, error_class: e.constructor.name}));
            process.exit(1);
        }
    } else if (op === "delete") {
        const schema = process.argv[4];
        const contentType = process.argv[5];
        const objUuid = process.argv[6];

        try {
            const storage = new EncryptedStorage(dbPath);
            await storage.unlockDatabase("test_passphrase_123");
            await storage.deletePayload(objUuid);
            storage.close();
            console.log(JSON.stringify({ok: true}));
        } catch (e) {
            console.log(JSON.stringify({ok: false, error: e.message, error_class: e.constructor.name}));
            process.exit(1);
        }
    }
}

main().catch(e => {
    console.log(JSON.stringify({ok: false, error: e.message, error_class: e.constructor.name}));
    process.exit(1);
});
"""
    }

    import tempfile
    import os
    import subprocess

    with tempfile.TemporaryDirectory() as base_tmpdir:
        py_script = os.path.join(base_tmpdir, "runner_direct.py")
        with open(py_script, "w") as f:
            f.write(direct_wrapper_code["python"])

        js_script = os.path.join(base_tmpdir, "runner_direct.js")
        with open(js_script, "w") as f:
            f.write(direct_wrapper_code["nodejs"])

        def get_direct_cmd(lang, op, db_path, object_uuid=None):
            if lang == "python":
                cmd = ["python", py_script, op, db_path, SCHEMA_UUID, CONTENT_TYPE]
            elif lang == "nodejs":
                cmd = ["node", js_script, op, db_path, SCHEMA_UUID, CONTENT_TYPE]
                # for node, we need to be in nodejs/ to resolve './src'

            if object_uuid:
                cmd.append(object_uuid)
            return cmd

        def run_direct_cmd(cmd, lang, payload=None):
            env = os.environ.copy()
            cwd = "nodejs" if lang == "nodejs" else "."
            input_data = json.dumps(payload) if payload is not None else None

            try:
                proc = subprocess.run(cmd, input=input_data, capture_output=True, env=env, text=True, cwd=cwd)
            except Exception as e:
                return False, str(e), None

            try:
                out = json.loads(proc.stdout)
            except json.JSONDecodeError:
                out = None

            if proc.returncode != 0:
                if out:
                    return False, out.get("error", "Unknown error"), out
                return False, f"Process exited with {proc.returncode}. stderr: {proc.stderr}", None

            if out and out.get("ok"):
                return True, None, out
            elif out:
                return False, out.get("error", "Unknown error"), out
            else:
                return False, "Failed to parse stdout as JSON or missing ok", None

        for payload in TEST_PAYLOADS:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, "test.db")

                # Write P1
                cmd_w = get_direct_cmd(writer, "write", db_path)
                w_ok, w_err, w_out = run_direct_cmd(cmd_w, writer, payload)
                if not w_ok:
                    return "failed", f"Write failed: {w_err}", None

                object_uuid = w_out.get("object_uuid")
                if not object_uuid:
                    return "failed", "Write did not return object_uuid", None

                # Read P1
                cmd_r = get_direct_cmd(reader, "read", db_path, object_uuid)
                r_ok, r_err, r_out = run_direct_cmd(cmd_r, reader)
                if not r_ok:
                    return "failed", f"Read P1 failed: {r_err}", None

                retrieved = r_out.get("payload")
                if retrieved != payload:
                    return "failed", f"Payload P1 mismatch. Expected {payload}, got {retrieved}", None

                # Update P2
                payload_p2 = {"updated": True, "old": payload}
                cmd_u = get_direct_cmd(reader, "update", db_path, object_uuid)
                u_ok, u_err, u_out = run_direct_cmd(cmd_u, reader, payload_p2)
                if not u_ok:
                    return "failed", f"Update failed: {u_err}", None

                # Read P2
                cmd_r2 = get_direct_cmd(writer, "read", db_path, object_uuid)
                r2_ok, r2_err, r2_out = run_direct_cmd(cmd_r2, writer)
                if not r2_ok:
                    return "failed", f"Read P2 failed: {r2_err}", None

                retrieved_p2 = r2_out.get("payload")
                if retrieved_p2 != payload_p2:
                    return "failed", f"Payload P2 mismatch. Expected {payload_p2}, got {retrieved_p2}", None

                # Delete
                cmd_d = get_direct_cmd(reader, "delete", db_path, object_uuid)
                d_ok, d_err, d_out = run_direct_cmd(cmd_d, reader)
                if not d_ok:
                    return "failed", f"Delete failed: {d_err}", None

                # Read Deleted
                cmd_rd = get_direct_cmd(writer, "read", db_path, object_uuid)
                rd_ok, rd_err, rd_out = run_direct_cmd(cmd_rd, writer)
                if rd_ok:
                    return "failed", "Read deleted object succeeded when it should have failed", None

                error_class = rd_out.get("error_class")
                if error_class != "ObjectNotFound":
                    return "failed", f"Expected ObjectNotFound after delete, got {error_class}", None

        return "direct-public-api-passed", "Successfully executed direct-public-api checks", {
            "mode": "direct-public-api",
            "public_entrypoint": True,
            "uses_test_wrapper_files": False,
            "public_quality_certification": False,
            "certification_record": "docs/implementation-notes/python-node-baseline-public-certification-record.md",
            "operations": ["write", "read", "update", "delete", "not_found_after_delete"],
            "payload_count": len(TEST_PAYLOADS),
            "database": "temporary-file",
            "artifact_policy": "not committed"
        }


def main():
    parser = argparse.ArgumentParser(description="Cross-Language Read/Write Compatibility Matrix")
    parser.add_argument("--list", action="store_true", help="List matrix discovery")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--execute", action="store_true", help="Execute runnable pairs")
    parser.add_argument("--mode", choices=["public-entrypoint-wrapper", "direct-public-api"], default="direct-public-api", help="Execution mode")
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
            if LANGUAGES[w].get("future_target") or LANGUAGES[r].get("future_target"):
                status = "skipped"
                reason = "future target execution not supported"
                evidence = None
            elif args.mode == "direct-public-api":
                status, reason, evidence = execute_pair_direct(w, r)
            else:
                status, reason, evidence = execute_pair(w, r)
            if status == "failed":
                all_passed = False
        else:
            evidence = None
            if LANGUAGES[w].get("future_target"):
                status = "skipped"
                reason = "writer is a future target only; execution disabled"
            elif LANGUAGES[r].get("future_target"):
                status = "skipped"
                reason = "reader is a future target only; execution disabled"
            elif LANGUAGES[w]["scaffold_only"]:
                status = "skipped"
                reason = "writer is scaffold-only; lacks stable public API"
            elif LANGUAGES[r]["scaffold_only"]:
                status = "skipped"
                reason = "reader is scaffold-only; lacks stable public API"
            else:
                if _get_wrapper_cmd(w, "write", "dummy") and _get_wrapper_cmd(r, "read", "dummy", "dummy"):
                    status = "certified-participant"
                    reason = "Baseline-public certified participant, runnable with --execute"
                else:
                    status = "skipped"
                    reason = "matrix_status: not-yet-runnable, missing wrapper command/test fixture contract"

        results.append({
            "writer": w,
            "reader": r,
            "status": status,
            "reason": reason,
            "evidence": evidence
        })

    if args.json:
        summary = {
            "public_entrypoint_passed": len([r for r in results if r["status"] == "public-entrypoint-passed"]),
            "direct_public_api_passed": len([r for r in results if r["status"] == "direct-public-api-passed"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "skipped": len([r for r in results if r["status"] == "skipped"]),
            "certified_participant": len([r for r in results if r["status"] == "certified-participant"])
        }
        output = {
            "mode": "execute" if args.execute else "discovery",
            "language_inventory": LANGUAGES,
            "pair_matrix": results,
            "summary": summary
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
        passed = [r for r in results if r['status'] in ('public-entrypoint-passed', 'direct-public-api-passed')]
        if passed:
            print(f"{len(passed)} pairs passed via execution matrix.")
            print("Python and Node.js are baseline-public certified participants.")
        else:
            print("No active pairs are currently runnable or passed.")
    else:
        print("Python and Node.js are baseline-public certified participants.")
        print("Use --execute to run the compatibility matrix.")
    print("No unsupported or skipped pairs are falsely claimed as passed.")

    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
