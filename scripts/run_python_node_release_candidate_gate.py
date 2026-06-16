import sys
import json
import argparse
import subprocess
import os
import urllib.request
import urllib.error
import glob
import re

def run_command(cmd, cwd=None, env=None):
    res = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def check_python_metadata():
    pyproject_path = "python/pyproject.toml"
    if not os.path.exists(pyproject_path):
        return {"ok": False, "error": "python/pyproject.toml not found"}

    with open(pyproject_path, "r") as f:
        content = f.read()

    name = None
    version = None
    has_readme = False
    has_license = False
    has_authors = False
    has_urls = False
    has_requires_python = False
    has_schema = False

    for line in content.splitlines():
        line = line.strip()
        if line.startswith('name = '):
            name = line.split('=')[1].strip().strip('"').strip("'")
        elif line.startswith('version = '):
            version = line.split('=')[1].strip().strip('"').strip("'")
        elif line.startswith('readme = '):
            has_readme = True
        elif line.startswith('license = '):
            has_license = True
        elif line.startswith('authors = '):
            has_authors = True
        elif line.startswith('[project.urls]'):
            has_urls = True
        elif line.startswith('requires-python = '):
            has_requires_python = True
        elif 'schema.sql' in line and 'package-data' in content:
            has_schema = True

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    version_valid = version and bool(semver_pattern.match(version))

    no_publishing_claims = "published" not in content.lower()

    ok = bool(name and version_valid and has_readme and has_license and has_authors and has_urls and has_requires_python and has_schema and no_publishing_claims)
    return {
        "ok": ok,
        "name": name,
        "version": version,
        "version_valid": version_valid,
        "has_readme": has_readme,
        "has_license": has_license,
        "has_authors": has_authors,
        "has_urls": has_urls,
        "has_requires_python": has_requires_python,
        "has_schema": has_schema,
        "no_publishing_claims": no_publishing_claims
    }

def check_node_metadata():
    package_json_path = "nodejs/package.json"
    if not os.path.exists(package_json_path):
        return {"ok": False, "error": "nodejs/package.json not found"}

    with open(package_json_path, "r") as f:
        data = json.load(f)

    name = data.get("name")
    version = data.get("version")

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    version_valid = version and bool(semver_pattern.match(version))

    has_description = "description" in data
    has_repository = "repository" in data
    has_license = "license" in data
    has_author = "author" in data
    has_files = "files" in data
    has_main = "main" in data and data["main"] == "src/index.js"

    content_str = json.dumps(data).lower()
    no_publishing_claims = "published" not in content_str

    ok = bool(name and version_valid and has_description and has_repository and has_license and has_author and has_files and has_main and no_publishing_claims)
    return {
        "ok": ok,
        "name": name,
        "version": version,
        "version_valid": version_valid,
        "has_description": has_description,
        "has_repository": has_repository,
        "has_license": has_license,
        "has_author": has_author,
        "has_files": has_files,
        "has_main": has_main,
        "no_publishing_claims": no_publishing_claims
    }

def check_documents():
    notes_path = "docs/implementation-notes/python-node-first-public-release-notes-draft.md"
    gov_path = "docs/implementation-notes/python-node-first-public-release-governance.md"

    notes_ok = os.path.exists(notes_path)
    gov_ok = os.path.exists(gov_path)

    return {
        "ok": notes_ok and gov_ok,
        "release_notes_draft_present": notes_ok,
        "governance_document_present": gov_ok
    }

def check_artifacts():
    # Check for tracked or untracked .whl, .tar.gz in specific dist paths that shouldn't be committed
    bad_files = []

    for root, dirs, files in os.walk("python"):
        if "node_modules" in root or "__pycache__" in root: continue
        for f in files:
            if f.endswith(".whl") or f.endswith(".tar.gz"):
                bad_files.append(os.path.join(root, f))

    for root, dirs, files in os.walk("nodejs"):
        if "node_modules" in root: continue
        for f in files:
            if f.endswith(".tgz"):
                bad_files.append(os.path.join(root, f))

    return {
        "ok": len(bad_files) == 0,
        "generated_artifacts_found": bad_files
    }

def probe_network(py_name, node_name):
    res = {}
    if py_name:
        try:
            req = urllib.request.Request(f"https://pypi.org/pypi/{py_name}/json", method="GET")
            urllib.request.urlopen(req, timeout=5)
            res["pypi_name"] = "taken"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                res["pypi_name"] = "available"
            else:
                res["pypi_name"] = "unknown"
        except Exception:
            res["pypi_name"] = "unknown"

    if node_name:
        try:
            req = urllib.request.Request(f"https://registry.npmjs.org/{node_name}", method="GET")
            urllib.request.urlopen(req, timeout=5)
            res["npm_name"] = "taken"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                res["npm_name"] = "available"
            else:
                res["npm_name"] = "unknown"
        except Exception:
            res["npm_name"] = "unknown"

    return res

def main():
    parser = argparse.ArgumentParser(description="First Public Release Candidate Gate")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--installed-matrix", action="store_true")
    parser.add_argument("--write-report", type=str)
    parser.add_argument("--allow-network-probes", action="store_true")
    args = parser.parse_args()

    results = {
        "phase": "first-public-release-candidate-gate",
        "publishing_performed": False,
        "credentials_required": False,
        "credentials_present": False,
        "storage_format_v1_semantics_changed": False,
        "tag_created": False,
        "artifact_publication": False,
        "release_candidate_freeze_ready": False,
        "remaining_blockers": []
    }

    # Run preflight
    preflight_cmd = [sys.executable, "scripts/run_python_node_release_preflight.py", "--json"]
    if args.installed_matrix:
        preflight_cmd.append("--installed-matrix")

    rc, stdout, stderr = run_command(preflight_cmd)
    try:
        preflight_res = json.loads(stdout)
        results["preflight"] = preflight_res
        if not preflight_res.get("python", {}).get("ok") or not preflight_res.get("node", {}).get("ok"):
            results["remaining_blockers"].append("Preflight checks failed.")
    except Exception as e:
        results["preflight"] = {"ok": False, "error": f"Failed to parse preflight output: {e}"}
        results["remaining_blockers"].append("Preflight script failed to return valid JSON.")

    py_meta = check_python_metadata()
    node_meta = check_node_metadata()

    results["python"] = py_meta
    results["node"] = node_meta

    if not py_meta.get("ok"):
        results["remaining_blockers"].append("Python metadata validation failed.")
    if not node_meta.get("ok"):
        results["remaining_blockers"].append("Node.js metadata validation failed.")

    if py_meta.get("version") != node_meta.get("version"):
        results["remaining_blockers"].append(f"Version mismatch: Python={py_meta.get('version')} Node={node_meta.get('version')}")

    docs_meta = check_documents()
    results["governance"] = {"ok": docs_meta["governance_document_present"]}
    results["release_notes"] = {"ok": docs_meta["release_notes_draft_present"]}

    if not docs_meta.get("ok"):
        results["remaining_blockers"].append("Release notes draft or governance document missing.")

    artifacts_meta = check_artifacts()
    if not artifacts_meta.get("ok"):
        results["remaining_blockers"].append(f"Generated artifacts found in tree: {artifacts_meta['generated_artifacts_found']}")

    if args.allow_network_probes:
        probes = probe_network(py_meta.get("name"), node_meta.get("name"))
        results["network_probes"] = probes

    if len(results["remaining_blockers"]) == 0:
        results["release_candidate_freeze_ready"] = True

    if args.write_report:
        with open(args.write_report, "w") as f:
            json.dump(results, f, indent=2)

    if args.json:
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["release_candidate_freeze_ready"] else 1)

    print("\n--- Release Candidate Gate Summary ---", file=sys.stderr)
    print(f"Publishing Performed: {results['publishing_performed']}", file=sys.stderr)
    print(f"Tag Created: {results['tag_created']}", file=sys.stderr)
    print(f"RC Freeze Ready: {results['release_candidate_freeze_ready']}", file=sys.stderr)

    if results["remaining_blockers"]:
        print("\nRemaining Blockers:", file=sys.stderr)
        for b in results["remaining_blockers"]:
            print(f" - {b}", file=sys.stderr)

    if results["release_candidate_freeze_ready"]:
        print("\nSUCCESS: Release candidate freeze conditions met.", file=sys.stderr)
        sys.exit(0)
    else:
        print("\nFAILURE: Release candidate gate failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
