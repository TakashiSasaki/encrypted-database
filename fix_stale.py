with open('scripts/check_stale_docs.sh', 'r') as f:
    content = f.read()

# Remove the block from the end
block_to_move = """# 27. Narrow guards for public-entrypoint evidence
check_phrase "public-entrypoint-test-wrapper evidence means baseline-public certification" "Stale claim: public-entrypoint-test-wrapper evidence is still test-wrapper evidence, not certification"
check_phrase "public-entrypoint-test-wrapper evidence is equivalent to baseline-public certification" "Stale claim: public-entrypoint-test-wrapper evidence is still test-wrapper evidence, not certification"
check_phrase "test wrappers are no longer used" "Stale claim: test wrappers remain part of the evidence path via public entrypoints"
check_phrase "Python and Node.js are already baseline-public" "Stale claim: Python and Node.js are baseline candidates, not yet baseline-public"
"""

if block_to_move in content:
    content = content.replace('\n\n' + block_to_move, '')
    content = content.replace('\n' + block_to_move, '')
    content = content.replace(block_to_move, '')

# Insert it before END OF NEW RULES
content = content.replace('# END OF NEW RULES', block_to_move + '\n# END OF NEW RULES')

with open('scripts/check_stale_docs.sh', 'w') as f:
    f.write(content)
