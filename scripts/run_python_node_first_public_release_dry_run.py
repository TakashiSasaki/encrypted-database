import sys
import json
import argparse
import os
import subprocess

def run_script(script_path, extra_args):
    if not os.path.exists(script_path):
        return False, None
    cmd = [sys.executable, script_path, "--json"] + extra_args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            data = json.loads(res.stdout)
            return res.returncode == 0, data
        except json.JSONDecodeError:
            return False, None
    except Exception:
        return False, None

def main():
    parser = argparse.ArgumentParser(description="First Public Release Dry Run Aggregator")
    parser.add_argument("--json", action="store_true", help="Output pure JSON to stdout")
    parser.add_argument("--require-publication-ready", action="store_true", help="Exit non-zero if publication is not authorized and ready")
    parser.add_argument("--write-report", type=str, help="Path to write the dry-run report JSON")
    parser.add_argument("--allow-network-probes", action="store_true", help="Optional non-blocking network probes")
    parser.add_argument("--include-installed-matrix", action="store_true", help="Include installed matrix tests in preflight")
    args = parser.parse_args()

    # Preflight
    preflight_args = []
    if args.include_installed_matrix:
        preflight_args.append("--installed-matrix")
    pf_passed, pf_data = run_script("scripts/run_python_node_release_preflight.py", preflight_args)

    pf_checked = pf_data is not None
    im_checked = args.include_installed_matrix
    im_passed = False
    if pf_data and "installed_distribution_matrix" in pf_data:
        im_passed = pf_data["installed_distribution_matrix"].get("passed", False)

    # Release Candidate
    rc_args = []
    if args.allow_network_probes:
        rc_args.append("--allow-network-probes")
    rc_passed, rc_data = run_script("scripts/run_python_node_release_candidate_gate.py", rc_args)
    rc_checked = rc_data is not None

    # Publication Readiness
    pub_args = []
    if args.allow_network_probes:
        pub_args.append("--allow-network-probes")
    pub_passed, pub_data = run_script("scripts/run_python_node_publication_readiness_gate.py", pub_args)
    pub_checked = pub_data is not None

    publication_ready = pub_data.get("publication_ready", False) if pub_data else False
    publication_authorized = pub_data.get("publication_authorized", False) if pub_data else False
    remaining_blockers = pub_data.get("remaining_blockers", []) if pub_data else []
    next_human_decisions = pub_data.get("next_human_decisions", []) if pub_data else []

    registry_probes_requested = pub_data.get("registry_probes_requested", False) if pub_data else False
    registry_probe_results = pub_data.get("registry_probe_results", {}) if pub_data else {}

    results = {
        "phase": "first-public-release-dry-run",
        "preflight_checked": pf_checked,
        "preflight_passed": pf_passed,
        "installed_matrix_checked": im_checked,
        "installed_matrix_passed": im_passed,
        "release_candidate_gate_checked": rc_checked,
        "release_candidate_gate_passed": rc_passed,
        "publication_readiness_gate_checked": pub_checked,
        "publication_ready": publication_ready,
        "publication_authorized": publication_authorized,
        "registry_probes_requested": registry_probes_requested,
        "registry_probe_results": registry_probe_results,
        "publishing_performed": False,
        "credentials_present": False,
        "tag_created": False,
        "tag_pushed": False,
        "artifact_publication": False,
        "storage_format_v1_semantics_changed": False,
        "remaining_blockers": remaining_blockers,
        "next_human_decisions": next_human_decisions
    }

    if args.write_report:
        with open(args.write_report, "w") as f:
            json.dump(results, f, indent=2)

    if args.json:
        print(json.dumps(results, indent=2))
        if args.require_publication_ready and not publication_ready:
            sys.exit(1)
        sys.exit(0)

    print("\n--- First Public Release Dry-Run Summary ---", file=sys.stderr)
    print(f"Preflight Passed: {pf_passed}", file=sys.stderr)
    print(f"Release Candidate Passed: {rc_passed}", file=sys.stderr)
    print(f"Publication Ready: {publication_ready}", file=sys.stderr)

    if args.include_installed_matrix:
        print(f"Installed Matrix Passed: {im_passed}", file=sys.stderr)

    if remaining_blockers:
        print("\nRemaining Human Blockers:", file=sys.stderr)
        for b in remaining_blockers:
            print(f" - {b}", file=sys.stderr)

    if registry_probes_requested:
        print(f"\nRegistry Probes: {registry_probe_results}", file=sys.stderr)

    if args.require_publication_ready and not publication_ready:
        print("\nFAILURE: Publication is not ready.", file=sys.stderr)
        sys.exit(1)

    # Defaults to informational success
    sys.exit(0)

if __name__ == "__main__":
    main()
