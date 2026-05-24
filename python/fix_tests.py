import re

with open('python/tests/test_metadata.py', 'r') as f:
    content = f.read()

# Replace simple cases
content = re.sub(
    r'    storage\d+ = EncryptedStorage\([^)]+\)\n    with pytest.raises\([^)]+\):\n        storage\d+\.unlock_database\([^)]+\)\n    storage\d+\.close\(\)\n',
    lambda m: m.group(0).replace("    with pytest.raises", "    try:\n        with pytest.raises").replace("    storage", "    finally:\n        storage", 1) if "finally" not in m.group(0) else m.group(0),
    content
)

def fix_block(match):
    lines = match.group(0).split('\n')
    out = []
    has_try = False
    for i, line in enumerate(lines):
        if line.strip().startswith('storage') and '= EncryptedStorage' in line:
            out.append(line)
            if lines[i+1].strip().startswith('with pytest.raises'):
                out.append('    try:')
                has_try = True
        elif line.strip().startswith('with pytest.raises'):
            if has_try:
                out.append('    ' + line)
            else:
                out.append(line)
        elif line.strip().startswith('storage') and '.unlock_database' in line:
            if has_try:
                out.append('    ' + line)
            else:
                out.append(line)
        elif line.strip().startswith('storage') and '.close()' in line:
            if has_try:
                out.append('    finally:')
                out.append('    ' + line)
                has_try = False
            else:
                out.append(line)
        else:
            if line.strip():
                if has_try and line.startswith('        '):
                    out.append('    ' + line)
                else:
                    out.append(line)
            else:
                out.append(line)
    return '\n'.join(out)

# Let's just do a simpler search and replace for the common pattern.
import sys

def manually_fix(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for pattern:
        # storageN = EncryptedStorage(db_path)
        # with pytest.raises(Exception):
        #     storageN.unlock_database(...)
        # storageN.close()

        match_storage = re.match(r'^(\s+)(storage\d*)\s*=\s*EncryptedStorage', line)
        if match_storage:
            indent = match_storage.group(1)
            storage_var = match_storage.group(2)

            # Look ahead to see if it matches the pattern
            if i + 3 < len(lines):
                l1 = lines[i+1]
                l2 = lines[i+2]
                l3 = lines[i+3]

                if l1.startswith(f"{indent}with pytest.raises") and \
                   l2.startswith(f"{indent}    {storage_var}.unlock_database") and \
                   l3.startswith(f"{indent}{storage_var}.close()"):

                    new_lines.append(line)
                    new_lines.append(f"{indent}try:\n")
                    new_lines.append(f"    {l1}")
                    new_lines.append(f"    {l2}")
                    new_lines.append(f"{indent}finally:\n")
                    new_lines.append(f"    {indent}{storage_var}.close()\n")
                    i += 4
                    continue

        new_lines.append(line)
        i += 1

    with open(file_path, 'w') as f:
        f.writelines(new_lines)

manually_fix('python/tests/test_metadata.py')
