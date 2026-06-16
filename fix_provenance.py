with open("scripts/run_python_node_release_preflight.py", "r") as f:
    content = f.read()

# The review said: "failed to actually modify scripts/run_python_node_release_preflight.py to enforce the environment isolation as requested (e.g., explicitly popping PYTHONPATH/NODE_PATH from the subprocess environment, or passing root paths via env variables to the generated script)."
# Actually, the script already has:
#             if "PYTHONPATH" in env:
#                 del env["PYTHONPATH"]
# But let's add REPO_ROOT into the wrapper scripts and explicitly check it

# py_wrapper
old_py_wrapper = """import sys
import json
import uuid
from encrypted_storage import EncryptedStorage

def main():
    op = sys.argv[1]
    db_path = sys.argv[2]
"""

new_py_wrapper = """import sys
import os
import json
import uuid
import encrypted_storage
from encrypted_storage import EncryptedStorage

def main():
    op = sys.argv[1]
    db_path = sys.argv[2]

    # Assert isolation
    repo_root = os.environ.get("EXPECTED_REPO_ROOT", "")
    prov_path = os.path.abspath(encrypted_storage.__file__)
    if repo_root and prov_path.startswith(repo_root + os.sep):
        print(json.dumps({"ok": False, "error": "Provenance isolation failed: inside repo root"}))
        sys.exit(0)
    if "site-packages" not in prov_path:
        print(json.dumps({"ok": False, "error": "Provenance isolation failed: not in site-packages"}))
        sys.exit(0)

"""

content = content.replace(old_py_wrapper, new_py_wrapper)


# node_wrapper
old_node_wrapper = """const fs = require('fs');
const { EncryptedStorage, ObjectNotFound } = require('encrypted-storage');

async function run() {
    try {
        const op = process.argv[2];
        const dbPath = process.argv[3];
"""

new_node_wrapper = """const fs = require('fs');
const path = require('path');
const { EncryptedStorage, ObjectNotFound } = require('encrypted-storage');

async function run() {
    try {
        const op = process.argv[2];
        const dbPath = process.argv[3];

        // Assert isolation
        const repoRoot = process.env.EXPECTED_REPO_ROOT || "";
        const provPath = path.resolve(require.resolve('encrypted-storage'));
        if (repoRoot && provPath.startsWith(repoRoot + path.sep)) {
             console.log(JSON.stringify({ok: false, error: "Provenance isolation failed: inside repo root"}));
             process.exit(0);
        }
        if (!provPath.includes("node_modules")) {
             console.log(JSON.stringify({ok: false, error: "Provenance isolation failed: not in node_modules"}));
             process.exit(0);
        }
"""

content = content.replace(old_node_wrapper, new_node_wrapper)

# Update run_wrapper to set EXPECTED_REPO_ROOT
old_run_wrapper_env = """        if lang == "python":
            python_bin = os.path.join(env_path, "bin", "python")
            if os.name == "nt":
                python_bin = os.path.join(env_path, "Scripts", "python")
            cmd = [python_bin, wrapper_path, op, db_path]
            # Avoid PYTHONPATH and ensure isolation
            env = os.environ.copy()
            if "PYTHONPATH" in env:
                del env["PYTHONPATH"]
        else: # node
            cmd = ["node", wrapper_path, op, db_path]
            # Make sure we use the Node env's modules
            cwd = env_path
            wrapper_path = os.path.abspath(wrapper_path) # Absolute path since cwd is different
            cmd[1] = wrapper_path
            env = os.environ.copy()
            if "NODE_PATH" in env:
                del env["NODE_PATH"]"""

new_run_wrapper_env = """        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env = os.environ.copy()
        env["EXPECTED_REPO_ROOT"] = repo_root

        if lang == "python":
            python_bin = os.path.join(env_path, "bin", "python")
            if os.name == "nt":
                python_bin = os.path.join(env_path, "Scripts", "python")
            cmd = [python_bin, wrapper_path, op, db_path]
            # Avoid PYTHONPATH and ensure isolation
            if "PYTHONPATH" in env:
                del env["PYTHONPATH"]
        else: # node
            cmd = ["node", wrapper_path, op, db_path]
            # Make sure we use the Node env's modules
            cwd = env_path
            wrapper_path = os.path.abspath(wrapper_path) # Absolute path since cwd is different
            cmd[1] = wrapper_path
            if "NODE_PATH" in env:
                del env["NODE_PATH"]"""

content = content.replace(old_run_wrapper_env, new_run_wrapper_env)


with open("scripts/run_python_node_release_preflight.py", "w") as f:
    f.write(content)
