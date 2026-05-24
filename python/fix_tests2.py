import re

def manually_fix2(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        match_storage = re.match(r'^(\s+)(storage\d*)\s*=\s*EncryptedStorage', line)
        if match_storage:
            indent = match_storage.group(1)
            storage_var = match_storage.group(2)

            # Look ahead for storage.unlock_database without raises
            if i + 3 < len(lines):
                l1 = lines[i+1]
                l2 = lines[i+2]
                l3 = lines[i+3]

                if l1.startswith(f"{indent}{storage_var}.unlock_database") and \
                   l2.startswith(f"{indent}assert {storage_var}.is_unlocked()") and \
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

manually_fix2('python/tests/test_metadata.py')
