import json
import sys
import os

def escape_c_string(s):
    if s is None:
        return '""'
    if '\0' in s:
        raise ValueError("Embedded NUL characters are not supported in the C/C++ AAD test harness generator.")

    out = []
    for char in s:
        if char == '"':
            out.append('\\"')
        elif char == '\\':
            out.append('\\\\')
        elif char == '\n':
            out.append('\\n')
        elif char == '\r':
            out.append('\\r')
        elif char == '\t':
            out.append('\\t')
        elif char == '\b':
            out.append('\\b')
        elif char == '\f':
            out.append('\\f')
        elif ord(char) < 0x20:
            # Use 3-digit octal escape to avoid ambiguity with trailing hex chars
            out.append(f'\\{ord(char):03o}')
        else:
            out.append(char)

    return '"' + "".join(out) + '"'

def generate_header(json_path, out_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        vectors = json.load(f)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("#ifndef GENERATED_AAD_VECTORS_H\n")
        f.write("#define GENERATED_AAD_VECTORS_H\n\n")

        f.write("typedef struct {\n")
        f.write("    const char* name;\n")
        f.write("    const char* policy;\n")
        f.write("    const char* expected_string;\n")
        f.write("    const char* expected_hex;\n")
        f.write("    const char* object_uuid;\n")
        f.write("    const char* schema_uuid;\n")
        f.write("    const char* content_type;\n")
        f.write("    const char* kid;\n")
        f.write("    const char* alg;\n")
        f.write("    const char* wrapped_kid;\n")
        f.write("    const char* wrapping_kid;\n")
        f.write("} AadTestVector;\n\n")

        f.write(f"static const AadTestVector AAD_TEST_VECTORS[] = {{\n")

        for v in vectors:
            inp = v.get("input", {})
            f.write("    {\n")
            f.write(f"        {escape_c_string(v.get('name'))},\n")
            f.write(f"        {escape_c_string(v.get('policy'))},\n")
            f.write(f"        {escape_c_string(v.get('expected_string'))},\n")
            f.write(f"        {escape_c_string(v.get('expected_hex'))},\n")
            f.write(f"        {escape_c_string(inp.get('object_uuid'))},\n")
            f.write(f"        {escape_c_string(inp.get('schema_uuid'))},\n")
            f.write(f"        {escape_c_string(inp.get('content_type'))},\n")
            f.write(f"        {escape_c_string(inp.get('kid'))},\n")
            f.write(f"        {escape_c_string(inp.get('alg'))},\n")
            f.write(f"        {escape_c_string(inp.get('wrapped_kid'))},\n")
            f.write(f"        {escape_c_string(inp.get('wrapping_kid'))}\n")
            f.write("    },\n")

        f.write("};\n\n")
        f.write(f"static const int NUM_AAD_TEST_VECTORS = {len(vectors)};\n\n")

        f.write("#endif /* GENERATED_AAD_VECTORS_H */\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_aad_test_vectors.py <input.json> <output.h>")
        sys.exit(1)

    generate_header(sys.argv[1], sys.argv[2])
