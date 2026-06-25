import re

with open('AGENTS.md', 'r') as f:
    content = f.read()

# For a cleaner approach, let's extract all list items and remove exact duplicates.
# However, sometimes they are not exact duplicates. One might contain more info.
# We will identify the specific bullet points and merge them if necessary, or just keep the longest one.

def deduplicate_bullet_prefix(text, prefix):
    # Find all bullets that start with the prefix
    pattern = r'(?m)^\*\s+\*\*' + re.escape(prefix) + r':\*\*(.*?)(?=\n\*\s+|\n\n|\Z)'
    matches = re.finditer(pattern, text, re.DOTALL)

    matches_list = list(matches)
    if len(matches_list) <= 1:
        return text

    # Merge contents
    merged_content = ""
    longest_match = max(matches_list, key=lambda m: len(m.group(1)))

    # Actually, we should just replace all occurrences with the longest one, and delete the rest

    for i, match in enumerate(matches_list):
        if match != longest_match:
            text = text.replace(match.group(0), '')

    # Remove empty lines that might have been left
    text = re.sub(r'\n\n+', '\n\n', text)
    return text

prefixes_to_dedup = [
    "JSON Canonicalization (JCS)",
    "UUID Validation",
    "Metadata Validation",
    "Release Candidate Gate",
    "Publication Readiness Gate",
    "Dry-Run Script",
    "GitHub Actions",
    "Documentation Guardrails",
    "Package Metadata",
    "UX Persona (Palette)",
    "PR Comments"
]

for prefix in prefixes_to_dedup:
    content = deduplicate_bullet_prefix(content, prefix)

# Also check for exact identical bullets without prefix
# E.g. web interfaces
web_if_pattern = r'(?m)^\*\s+\*\*Web Interfaces & Verification:\*\*(.*?)(?=\n\*\s+|\n\n|\Z)'
matches = re.finditer(web_if_pattern, content, re.DOTALL)
matches_list = list(matches)
if len(matches_list) > 1:
    longest_match = max(matches_list, key=lambda m: len(m.group(1)))
    for i, match in enumerate(matches_list):
        if match != longest_match:
            content = content.replace(match.group(0), '')

content = re.sub(r'\n\n+', '\n\n', content)

with open('AGENTS.md', 'w') as f:
    f.write(content)
print("Deduplicated AGENTS.md")
