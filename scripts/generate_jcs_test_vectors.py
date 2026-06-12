import json
import sys

def escape_c_string(s):
    if s is None:
        return '""'
    if '\0' in s:
        raise ValueError("Embedded NUL characters are not supported in the C/C++ JCS test harness generator.")

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
            out.append(f'\\{ord(char):03o}')
        else:
            out.append(char)

    return '"' + "".join(out) + '"'

def generate_node(data, index_state, header_f):
    node_index = index_state["node_index"]
    index_state["node_index"] += 1

    if isinstance(data, dict):
        if len(data) == 0:
            header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_OBJECT, {{ .object = {{ NULL, 0 }} }} }};\n")
            return node_index

        member_indices = []
        # Preserve original key order from python dict (which is insertion order)
        for k, v in data.items():
            val_idx = generate_node(v, index_state, header_f)
            member_indices.append((k, val_idx))

        member_array_name = f"obj_members_{node_index}"
        header_f.write(f"static const VaultJcsObjectMember {member_array_name}[] = {{\n")
        for k, val_idx in member_indices:
            header_f.write(f"    {{ {escape_c_string(k)}, &node_{val_idx} }},\n")
        header_f.write("};\n")

        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_OBJECT, {{ .object = {{ {member_array_name}, {len(member_indices)} }} }} }};\n")
        return node_index

    elif isinstance(data, list):
        if len(data) == 0:
            header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_ARRAY, {{ .array = {{ NULL, 0 }} }} }};\n")
            return node_index

        elem_indices = []
        for v in data:
            val_idx = generate_node(v, index_state, header_f)
            elem_indices.append(val_idx)

        elem_array_name = f"arr_elems_{node_index}"
        header_f.write(f"static const VaultJcsValue* const {elem_array_name}[] = {{\n")
        for val_idx in elem_indices:
            header_f.write(f"    &node_{val_idx},\n")
        header_f.write("};\n")

        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_ARRAY, {{ .array = {{ {elem_array_name}, {len(elem_indices)} }} }} }};\n")
        return node_index

    elif isinstance(data, str):
        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_STRING, {{ .string_val = {escape_c_string(data)} }} }};\n")
        return node_index

    elif isinstance(data, bool):
        # Must check bool before int, as bool is a subclass of int in Python
        val = "true" if data else "false"
        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_BOOLEAN, {{ .boolean_val = {val} }} }};\n")
        return node_index

    elif isinstance(data, int):
        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_INTEGER, {{ .integer_val = {data}LL }} }};\n")
        return node_index

    elif data is None:
        header_f.write(f"static const VaultJcsValue node_{node_index} = {{ VAULT_JCS_NULL, {{0}} }};\n")
        return node_index

    elif isinstance(data, float):
        raise ValueError("Floats are not supported by the C/C++ JCS test harness generator.")

    else:
        raise ValueError(f"Unsupported data type: {type(data)}")

import os

def generate_header(json_path, out_path):
    if os.path.basename(json_path) == "future-boundary-plan.json":
        raise ValueError(f"The input file {json_path} is planning-only and must not be consumed by the current generated-AST scaffold.")

    with open(json_path, 'r', encoding='utf-8') as f:
        vectors = json.load(f)

    for v in vectors:
        for restricted_key in ["future_only", "expected_error", "input_raw_json"]:
            if restricted_key in v:
                raise ValueError(f"Vector '{v.get('name')}' contains planning/rejection-only key '{restricted_key}'. This vector is not safe for current generated-AST consumption.")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("#ifndef GENERATED_JCS_VECTORS_H\n")
        f.write("#define GENERATED_JCS_VECTORS_H\n\n")
        f.write("#include \"vault_jcs_internal.h\"\n\n")

        index_state = {"node_index": 0}
        vector_node_indices = []

        for v in vectors:
            inp = v["input"]
            idx = generate_node(inp, index_state, f)
            vector_node_indices.append(idx)

        f.write("\nstatic const JcsTestVector JCS_TEST_VECTORS[] = {\n")
        for i, v in enumerate(vectors):
            f.write("    {\n")
            f.write(f"        {escape_c_string(v.get('name'))},\n")
            f.write(f"        {escape_c_string(v.get('description'))},\n")
            f.write(f"        &node_{vector_node_indices[i]},\n")
            f.write(f"        {escape_c_string(v.get('expected_string'))},\n")
            f.write(f"        {escape_c_string(v.get('expected_hex'))}\n")
            f.write("    },\n")
        f.write("};\n\n")

        f.write(f"static const int NUM_JCS_TEST_VECTORS = {len(vectors)};\n\n")
        f.write("#endif /* GENERATED_JCS_VECTORS_H */\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_jcs_test_vectors.py <input.json> <output.h>")
        sys.exit(1)

    generate_header(sys.argv[1], sys.argv[2])
