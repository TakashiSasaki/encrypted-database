import sys
import json
import argparse
import os
import re
import subprocess
import urllib.request
import urllib.error

def check_human_blockers(decision_record_path):
    blockers = []
    placeholders_remaining = 0
    decision_record_status = "unknown"
    manual_decisions = {}

    if not os.path.exists(decision_record_path):
        blockers.append(f"Decision record not found at {decision_record_path}")
        return blockers, placeholders_remaining, decision_record_status, manual_decisions

    with open(decision_record_path, "r") as f:
        content = f.read()

    lines = content.splitlines()
    for line in lines:
        if "Status:" in line:
            if "PENDING" in line:
                decision_record_status = "pending"
                blockers.append("Decision record status is PENDING.")
            elif "APPROVED" in line:
                decision_record_status = "approved"

        if "PENDING" in line or "PLACEHOLDER" in line:
            placeholders_remaining += 1
            if "PyPI Account" in line or "PyPI Project/Account Decision:" in line:
                blockers.append("PyPI project/account decision is pending.")
                manual_decisions["pypi_account"] = "pending"
            elif "npm Account" in line or "npm Package/Scope/Account Decision:" in line:
                blockers.append("npm package/scope/account decision is pending.")
                manual_decisions["npm_account"] = "pending"
            elif "Trusted Publishing Configuration:" in line or "Trusted Publishing/Token Decision:" in line:
                blockers.append("Trusted publishing/token configuration decisions are pending.")
                manual_decisions["trusted_publishing"] = "pending"
            elif "Approver:" in line or "Release Manager Approval:" in line:
                blockers.append("Manual approval decision is pending.")
                manual_decisions["manual_approval"] = "pending"
            elif "Candidate Commit SHA:" in line:
                blockers.append("Candidate Commit SHA is a placeholder.")
                manual_decisions["candidate_commit_sha"] = "pending"
            elif "Gate Result:" in line:
                blockers.append("Gate Result is a placeholder.")
                manual_decisions["gate_result"] = "pending"

    # Explicit verifications
    if "Publication Authorized: false" in content:
        blockers.append("Publication is not authorized.")
    if "Publishing Performed: true" in content:
        blockers.append("Actual publication is incorrectly claimed as performed.")
    if "Credentials Present: true" in content:
        blockers.append("Credentials are incorrectly claimed as present.")
    if "Trusted Publishing Configured: true" in content:
        blockers.append("Trusted publishing is incorrectly claimed as configured.")
    if "Release Tag Created: true" in content:
        blockers.append("Release tag is incorrectly claimed as created.")
    if "Release Tag Pushed: true" in content:
        blockers.append("Release tag is incorrectly claimed as pushed.")
    if "Storage Format V1 Semantics Changed: true" in content:
        blockers.append("Storage Format V1 semantics are incorrectly claimed as changed.")

    return blockers, placeholders_remaining, decision_record_status, manual_decisions

def run_release_candidate_gate():
    rc_checked = False
    rc_passed = False
    rc_freeze_ready = False

    script_path = "scripts/run_python_node_release_candidate_gate.py"
    if os.path.exists(script_path):
        rc_checked = True
        try:
            res = subprocess.run([sys.executable, script_path, "--json"], capture_output=True, text=True)
            try:
                data = json.loads(res.stdout)
                rc_passed = res.returncode == 0
                rc_freeze_ready = data.get("release_candidate_freeze_ready", False)
            except json.JSONDecodeError:
                pass
        except Exception:
            pass

    return rc_checked, rc_passed, rc_freeze_ready

def probe_network():
    return {
        "note": "Network probes for publication readiness are not implemented in this script. Registry/name checks remain manual."
    }

def main():
    parser = argparse.ArgumentParser(description="First Public Release Publication Readiness Gate")
    parser.add_argument("--json", action="store_true", help="Output pure JSON to stdout")
    parser.add_argument("--require-publication-ready", action="store_true", help="Exit non-zero if publication is not authorized and ready")
    parser.add_argument("--write-report", type=str, help="Path to write the readiness report JSON")
    parser.add_argument("--decision-record", type=str, default="docs/implementation-notes/python-node-first-public-release-decision-record.md", help="Path to the decision record")
    parser.add_argument("--allow-network-probes", action="store_true", help="Optional non-blocking network probes")
    args = parser.parse_args()

    blockers, placeholders_remaining, decision_record_status, manual_decisions = check_human_blockers(args.decision_record)

    rc_checked, rc_passed, rc_freeze_ready = run_release_candidate_gate()
    if rc_checked and not rc_freeze_ready:
        blockers.append("Release candidate gate is not ready.")

    decision_record_found = os.path.exists(args.decision_record)
    publication_ready = len(blockers) == 0 and rc_freeze_ready and decision_record_found

    results = {
        "phase": "first-public-release-human-decision-gate",
        "decision_record_path": args.decision_record,
        "decision_record_found": decision_record_found,
        "decision_record_status": decision_record_status,
        "decision_record_placeholders_remaining": placeholders_remaining,
        "release_candidate_gate_checked": rc_checked,
        "release_candidate_gate_passed": rc_passed,
        "release_candidate_freeze_ready": rc_freeze_ready,
        "publication_ready": publication_ready,
        "publication_authorized": decision_record_status == "approved",
        "publishing_performed": False,
        "credentials_required": False,
        "credentials_present": False,
        "credentials_configured": False,
        "trusted_publishing_configured": False,
        "tag_created": False,
        "tag_pushed": False,
        "artifact_publication": False,
        "storage_format_v1_semantics_changed": False,
        "manual_decisions": manual_decisions,
        "remaining_blockers": blockers,
        "next_human_decisions": ["Approve release packet", "Create release tag", "Perform publication"] if blockers else []
    }

    if args.write_report:
        with open(args.write_report, "w") as f:
            json.dump(results, f, indent=2)

    if args.json:
        print(json.dumps(results, indent=2))
        if args.require_publication_ready and not publication_ready:
            sys.exit(1)
        sys.exit(0)

    print("\n--- Publication Readiness Gate Summary ---", file=sys.stderr)
    print(f"Publication Authorized: {results['publication_authorized']}", file=sys.stderr)
    print(f"Publication Ready: {results['publication_ready']}", file=sys.stderr)
    print(f"Credentials Configured: {results['credentials_configured']}", file=sys.stderr)
    print(f"Tag Created/Pushed: {results['tag_created']} / {results['tag_pushed']}", file=sys.stderr)

    if blockers:
        print("\nRemaining Blockers:", file=sys.stderr)
        for b in blockers:
            print(f" - {b}", file=sys.stderr)

    if args.allow_network_probes:
        print("\nNote: Network probes for publication readiness are not implemented in this script. Registry/name checks remain manual.", file=sys.stderr)

    if args.require_publication_ready and not publication_ready:
        print("\nFAILURE: Publication is not ready.", file=sys.stderr)
        sys.exit(1)

    # Default is informational success (exit 0) unless --require-publication-ready was requested.
    sys.exit(0)

if __name__ == "__main__":
    main()
