import re

with open('scripts/check_stale_docs.sh', 'r') as f:
    content = f.read()

# Find the duplicated 39. Java Guardrails section
# We can just look for the block starting with # 39. Java Guardrails
parts = content.split('# 39. Java Guardrails\n')
if len(parts) > 2:
    # It appears multiple times
    new_content = parts[0] + '# 39. Java Guardrails\n' + parts[1]
    # The second duplicate might have trailing stuff, let's see.
    print(f"Parts length: {len(parts)}")

with open('scripts/check_stale_docs.sh', 'r') as f:
    lines = f.readlines()

new_lines = []
in_java_guardrails = False
java_guardrails_seen = 0

for line in lines:
    if line.startswith('# 39. Java Guardrails'):
        java_guardrails_seen += 1
        if java_guardrails_seen > 1:
            in_java_guardrails = True
            continue
    if in_java_guardrails:
        if line.startswith('check_phrase') or line.strip() == '':
            continue
        else:
            in_java_guardrails = False
    if not in_java_guardrails:
        new_lines.append(line)

with open('scripts/check_stale_docs.sh', 'w') as f:
    f.writelines(new_lines)
print("Cleaned check_stale_docs.sh")
