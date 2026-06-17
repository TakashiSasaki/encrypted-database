import sys
import json
import argparse
import os
import re
import subprocess
import urllib.request
import urllib.error

def parse_pyproject_toml(path):
    if not os.path.exists(path):
        return None, None
    with open(path, "r") as f:
        content = f.read()

    if sys.version_info >= (3, 11):
        import tomllib
        try:
            data = tomllib.loads(content)
            project = data.get("project", {})
            return project.get("name"), project.get("version")
        except Exception:
            return None, None
    else:
        name, version = None, None
        in_project = False
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                in_project = (line == '[project]')
                continue
            if in_project and '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key == 'name':
                    name = val
                elif key == 'version':
                    version = val
        return name, version

def get_node_metadata(path):
    if not os.path.exists(path):
        return None, None
    with open(path, "r") as f:
        try:
            data = json.load(f)
            return data.get("name"), data.get("version")
        except Exception:
            return None, None

def check_human_blockers(decision_record_path, py_name, py_version, node_name, node_version, current_head):
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
                manual_decisions["status"] = "approved"

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

    # Match Candidate Commit SHA
    candidate_sha_match = re.search(r"Candidate Commit SHA:\s*([a-f0-9]+)", content, re.IGNORECASE)
    if candidate_sha_match:
        sha_val = candidate_sha_match.group(1)
        if sha_val.lower() != "placeholder":
            if sha_val != current_head:
                blockers.append(f"Candidate Commit SHA '{sha_val}' does not match HEAD '{current_head}'.")
                manual_decisions["candidate_commit_sha"] = "mismatch"
            else:
                manual_decisions["candidate_commit_sha"] = "resolved"

    # Check for inconsistencies
    if "Publication Authorized: false" in content:
        if decision_record_status == "approved":
            blockers.append("Inconsistent state: Status is APPROVED but Publication Authorized is false.")
        blockers.append("Publication is not authorized.")
        manual_decisions["publication_authorized"] = "false"
    elif "Publication Authorized: true" in content:
        if decision_record_status == "pending":
            blockers.append("Inconsistent state: Status is PENDING but Publication Authorized is true.")
        manual_decisions["publication_authorized"] = "true"

    if "Publishing Performed: true" in content:
        blockers.append("Actual publication is incorrectly claimed as performed.")
    if "Credentials Present: true" in content:
        blockers.append("Credentials are incorrectly claimed as present.")
    if "Trusted Publishing Configured: true" in content or "Trusted Publishing Setup Configured: true" in content:
        blockers.append("Trusted publishing is incorrectly claimed as configured.")
    if "Release Tag Created: true" in content:
        blockers.append("Release tag is incorrectly claimed as created.")
    if "Release Tag Pushed: true" in content:
        blockers.append("Release tag is incorrectly claimed as pushed.")
    if "Storage Format V1 Semantics Changed: true" in content:
        blockers.append("Storage Format V1 semantics are incorrectly claimed as changed.")

    # Match packages
    if py_name and py_version:
        if f"Python:** `{py_name}`" not in content and f"Python:** {py_name}" not in content:
            blockers.append(f"Decision record does not correctly specify Python package name '{py_name}'.")
        if f"(Version: {py_version})" not in content:
            blockers.append(f"Decision record does not correctly specify Python version '{py_version}'.")

    if node_name and node_version:
        if f"Node.js:** `{node_name}`" not in content and f"Node.js:** {node_name}" not in content:
            blockers.append(f"Decision record does not correctly specify Node.js package name '{node_name}'.")
        if f"(Version: {node_version})" not in content:
            blockers.append(f"Decision record does not correctly specify Node.js version '{node_version}'.")

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

def probe_registry(name, ecosystem):
    if not name:
        return "unknown"

    import urllib.parse
    if ecosystem == "pypi":
        url = f"https://pypi.org/pypi/{name}/json"
    elif ecosystem == "npm":
        safe_name = urllib.parse.quote(name, safe='@')
        url = f"https://registry.npmjs.org/{safe_name}"
    else:
        return "unknown"

    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                return "exists"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "not_found"
    except Exception:
        pass

    return "unknown"

def get_head_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def main():
    parser = argparse.ArgumentParser(description="First Public Release Execution Approval Readiness Gate")
    parser.add_argument("--json", action="store_true", help="Output pure JSON to stdout")
    parser.add_argument("--require-publication-ready", action="store_true", help="Exit non-zero if publication is not authorized and ready")
    parser.add_argument("--write-report", type=str, help="Path to write the readiness report JSON")
    parser.add_argument("--decision-record", type=str, default="docs/implementation-notes/python-node-first-public-release-decision-record.md", help="Path to the decision record")
    parser.add_argument("--allow-network-probes", action="store_true", help="Optional non-blocking network probes")
    args = parser.parse_args()

    py_name, py_version = parse_pyproject_toml("python/pyproject.toml")
    node_name, node_version = get_node_metadata("nodejs/package.json")
    current_head = get_head_sha()

    blockers, placeholders_remaining, decision_record_status, manual_decisions = check_human_blockers(
        args.decision_record, py_name, py_version, node_name, node_version, current_head
    )

    package_versions_match = (py_version == node_version) and (py_version is not None)
    if not package_versions_match:
        blockers.append("Python and Node.js package versions do not match.")

    if py_version != "0.1.0":
        blockers.append(f"Expected candidate version 0.1.0, found {py_version} (Python).")
    if node_version != "0.1.0":
        blockers.append(f"Expected candidate version 0.1.0, found {node_version} (Node.js).")

    rc_checked, rc_passed, rc_freeze_ready = run_release_candidate_gate()
    if rc_checked and not rc_freeze_ready:
        blockers.append("Release candidate gate is not ready.")

    decision_record_found = os.path.exists(args.decision_record)
    publication_ready = len(blockers) == 0 and rc_freeze_ready and decision_record_found and package_versions_match

    registry_probe_results = {}
    if args.allow_network_probes:
        registry_probe_results["python"] = probe_registry(py_name, "pypi")
        registry_probe_results["node"] = probe_registry(node_name, "npm")
        # Also probe the scoped NPM variant if we want, but let's just do default names for now.
        registry_probe_results["node_scoped"] = probe_registry("@vault/encrypted-storage", "npm")

    candidate_commit_matches_head = (manual_decisions.get("candidate_commit_sha") == "resolved")

    next_human_decisions = []
    if "pypi_account" in manual_decisions: next_human_decisions.append("Decide PyPI Account")
    if "npm_account" in manual_decisions: next_human_decisions.append("Decide npm Account")
    if "trusted_publishing" in manual_decisions: next_human_decisions.append("Configure Trusted Publishing")
    if "manual_approval" in manual_decisions: next_human_decisions.append("Obtain Release Manager Approval")
    if decision_record_status != "approved": next_human_decisions.append("Approve release packet")
    if placeholders_remaining > 0: next_human_decisions.append("Resolve placeholders in decision record")

    results = {
        "phase": "first-public-release-execution-approval-readiness",
        "decision_record_path": args.decision_record,
        "decision_record_found": decision_record_found,
        "decision_record_status": decision_record_status,
        "decision_record_placeholders_remaining": placeholders_remaining,
        "release_candidate_gate_checked": rc_checked,
        "release_candidate_gate_passed": rc_passed,
        "release_candidate_freeze_ready": rc_freeze_ready,
        "package_metadata_checked": True,
        "python_package_name": py_name,
        "python_package_version": py_version,
        "node_package_name": node_name,
        "node_package_version": node_version,
        "package_versions_match": package_versions_match,
        "candidate_commit_sha": current_head if candidate_commit_matches_head else "unknown",
        "current_head_sha": current_head,
        "candidate_commit_matches_head": candidate_commit_matches_head,
        "registry_probes_requested": args.allow_network_probes,
        "registry_probe_results": registry_probe_results,
        "publication_ready": publication_ready,
        "publication_authorized": decision_record_status == "approved" and not blockers,
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
        "next_human_decisions": list(dict.fromkeys(next_human_decisions))  # Unique list
    }

    if args.write_report:
        with open(args.write_report, "w") as f:
            json.dump(results, f, indent=2)

    if args.json:
        print(json.dumps(results, indent=2))
        if args.require_publication_ready and not publication_ready:
            sys.exit(1)
        sys.exit(0)

    print("\n--- Phase 14 Publication Readiness Gate Summary ---", file=sys.stderr)
    print(f"Publication Authorized: {results['publication_authorized']}", file=sys.stderr)
    print(f"Publication Ready: {results['publication_ready']}", file=sys.stderr)
    print(f"Package Metadata Checked: OK ({py_name} {py_version} | {node_name} {node_version})", file=sys.stderr)

    if blockers:
        print("\nRemaining Blockers:", file=sys.stderr)
        for b in blockers:
            print(f" - {b}", file=sys.stderr)

    if args.allow_network_probes:
        print(f"\nRegistry Probe Results: {registry_probe_results}", file=sys.stderr)

    if args.require_publication_ready and not publication_ready:
        print("\nFAILURE: Publication is not ready.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
