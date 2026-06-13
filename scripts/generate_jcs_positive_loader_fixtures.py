import argparse
import json
import sys
import os

def check_safe_integer(val):
    if isinstance(val, bool):
        return True
    if isinstance(val, int):
        return -9007199254740991 <= val <= 9007199254740991
    return False

def validate_input(val):
    if val is None:
        return True, ""
    if isinstance(val, bool):
        return True, ""
    if isinstance(val, int):
        if not check_safe_integer(val):
            return False, "unsafe integer"
        return True, ""
    if isinstance(val, float):
        return False, "float unsupported"
    if isinstance(val, str):
        if "\x00" in val:
            return False, "embedded NUL"
        try:
            val.encode('utf-8')
        except UnicodeEncodeError:
            return False, "invalid unicode"
        return True, ""
    if isinstance(val, list):
        for item in val:
            ok, reason = validate_input(item)
            if not ok:
                return False, f"array item: {reason}"
        return True, ""
    if isinstance(val, dict):
        for k, v in val.items():
            if "\x00" in k:
                return False, "embedded NUL in key"
            try:
                k.encode('utf-8')
            except UnicodeEncodeError:
                return False, "invalid unicode in key"
            ok, reason = validate_input(v)
            if not ok:
                return False, f"object key '{k}': {reason}"
        return True, ""
    return False, f"unknown type: {type(val)}"

def dump_c_declarations(val, prefix, f):
    if val is None:
        f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_NULL}};\n")
    elif isinstance(val, bool):
        f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_BOOLEAN, .value = {{.boolean_val = {'true' if val else 'false'}}} }};\n")
    elif isinstance(val, int) and not isinstance(val, bool):
        f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_INTEGER, .value = {{.integer_val = {val}LL}} }};\n")
    elif isinstance(val, str):
        encoded = val.encode('utf-8')
        escaped = ''.join(f'\\x{b:02x}' for b in encoded)
        f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_STRING, .value = {{.string_val = {{(const unsigned char*)\"{escaped}\", {len(encoded)}}}}} }};\n")
    elif isinstance(val, list):
        for i, item in enumerate(val):
            dump_c_declarations(item, f"{prefix}_item_{i}", f)

        if len(val) > 0:
            f.write(f"static VaultJcsTestJsonNode {prefix}_elements[] = {{\n")
            for i in range(len(val)):
                f.write(f"    {{0}},\n") # placeholder, will be initialized dynamically
            f.write("};\n")
            f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_ARRAY, .value = {{.array = {{{prefix}_elements, {len(val)}}}}} }};\n")

            f.write(f"static void {prefix}_init(void) {{\n")
            for i in range(len(val)):
                f.write(f"    {prefix}_elements[{i}] = {prefix}_item_{i};\n")
            f.write("}\n")
        else:
            f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_ARRAY, .value = {{.array = {{NULL, 0}}}} }};\n")
            f.write(f"static void {prefix}_init(void) {{}}\n")

    elif isinstance(val, dict):
        for i, (k, v) in enumerate(val.items()):
            dump_c_declarations(v, f"{prefix}_val_{i}", f)

        if len(val) > 0:
            f.write(f"static VaultJcsTestObjectMember {prefix}_members[] = {{\n")
            for i, (k, v) in enumerate(val.items()):
                encoded = k.encode('utf-8')
                escaped = ''.join(f'\\x{b:02x}' for b in encoded)
                f.write(f"    {{ {{(const unsigned char*)\"{escaped}\", {len(encoded)}}}, &{prefix}_val_{i} }},\n")
            f.write("};\n")
            f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_OBJECT, .value = {{.object = {{{prefix}_members, {len(val)}, false}}}} }};\n")
            f.write(f"static void {prefix}_init(void) {{\n")
            for i, (k, v) in enumerate(val.items()):
                f.write(f"    {prefix}_members[{i}].value = &{prefix}_val_{i};\n")
            f.write("}\n")
        else:
            f.write(f"static VaultJcsTestJsonNode {prefix} = {{.type = TEST_JSON_OBJECT, .value = {{.object = {{NULL, 0, false}}}} }};\n")
            f.write(f"static void {prefix}_init(void) {{}}\n")
    else:
        raise ValueError("unsupported")

def dump_cpp_declarations(val, prefix, f):
    if val is None:
        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::NULL_VAL }};\n")
    elif isinstance(val, bool):
        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::BOOLEAN, {'true' if val else 'false'} }};\n")
    elif isinstance(val, int) and not isinstance(val, bool):
        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::INTEGER, false, {val}LL }};\n")
    elif isinstance(val, str):
        encoded = val.encode('utf-8')
        escaped = ''.join(f'\\x{b:02x}' for b in encoded)
        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::STRING, false, 0, std::string(\"{escaped}\", {len(encoded)}) }};\n")
    elif isinstance(val, list):
        for i, item in enumerate(val):
            dump_cpp_declarations(item, f"{prefix}_item_{i}", f)

        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::ARRAY, false, 0, \"\", {{ ")
        for i in range(len(val)):
            f.write(f"&{prefix}_item_{i}, ")
        f.write("} };\n")

    elif isinstance(val, dict):
        for i, (k, v) in enumerate(val.items()):
            dump_cpp_declarations(v, f"{prefix}_val_{i}", f)

        f.write(f"static vault::jcs::test::JsonNode {prefix} {{ vault::jcs::test::JsonType::OBJECT, false, 0, \"\", {{}}, {{ ")
        for i, (k, v) in enumerate(val.items()):
            encoded = k.encode('utf-8')
            escaped = ''.join(f'\\x{b:02x}' for b in encoded)
            f.write(f"{{ std::string(\"{escaped}\", {len(encoded)}), &{prefix}_val_{i} }}, ")
        f.write("} };\n")
    else:
        raise ValueError("unsupported")

def _collect_c_init_calls(val, prefix, calls):
    if isinstance(val, list):
        for i, item in enumerate(val):
            _collect_c_init_calls(item, f"{prefix}_item_{i}", calls)
        calls.append(f"{prefix}_init()")
    elif isinstance(val, dict):
        for i, (k, v) in enumerate(val.items()):
            _collect_c_init_calls(v, f"{prefix}_val_{i}", calls)
        calls.append(f"{prefix}_init()")

def generate(c_out_path, cpp_out_path, input_files):
    all_vectors = []

    print("Generating generic positive loader fixtures...")
    for file_path in input_files:
        print(f"Processing {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            sys.exit(1)

        included = 0
        excluded = 0


        for vec in data:
            if not isinstance(vec, dict):
                print(f"  - excluded: <unnamed> (source: {file_path}, reason: vector is not a JSON object)")
                excluded += 1
                continue

            name = vec.get("name", "<unnamed>")

            allowed_keys = {"name", "description", "input", "expected_string", "expected_hex"}
            actual_keys = set(vec.keys())

            # Reject unknown metadata or rejection keys early
            if not actual_keys.issubset(allowed_keys):
                unknown_keys = actual_keys - allowed_keys
                print(f"  - excluded: {name} (source: {file_path}, reason: unknown or unsupported fields: {', '.join(unknown_keys)})")
                excluded += 1
                continue

            # Check required keys
            missing_keys = allowed_keys - actual_keys
            if missing_keys:
                print(f"  - excluded: {name} (source: {file_path}, reason: missing required fields: {', '.join(missing_keys)})")
                excluded += 1
                continue

            # Validate field types
            if not isinstance(vec["name"], str):
                print(f"  - excluded: {name} (source: {file_path}, reason: 'name' must be a string)")
                excluded += 1
                continue
            if not isinstance(vec["description"], str):
                print(f"  - excluded: {name} (source: {file_path}, reason: 'description' must be a string)")
                excluded += 1
                continue
            if not isinstance(vec["expected_string"], str):
                print(f"  - excluded: {name} (source: {file_path}, reason: 'expected_string' must be a string)")
                excluded += 1
                continue
            if not isinstance(vec["expected_hex"], str):
                print(f"  - excluded: {name} (source: {file_path}, reason: 'expected_hex' must be a string)")
                excluded += 1
                continue

            input_val = vec["input"]

            ok, reason = validate_input(input_val)
            if not ok:
                print(f"  - excluded: {name} (source: {file_path}, reason: input is unsupported: {reason})")
                excluded += 1
                continue

            print(f"  + included: {name}")
            all_vectors.append({
                "name": name,
                "input": input_val,
                "expected_string": vec["expected_string"],
                "expected_hex": vec["expected_hex"],
            })
            included += 1
        print(f"  Summary for {file_path}: included: {included}, excluded: {excluded}\n")

    print(f"Total vectors included: {len(all_vectors)}")

    # Generate C header
    if c_out_path:
        with open(c_out_path, 'w', encoding='utf-8') as f:
            f.write("/* GENERATED FILE - DO NOT EDIT */\n")
            f.write("#ifndef GENERATED_JCS_POSITIVE_LOADER_FIXTURES_H\n")
            f.write("#define GENERATED_JCS_POSITIVE_LOADER_FIXTURES_H\n\n")

            f.write("typedef struct {\n")
            f.write("    const char* name;\n")
            f.write("    VaultJcsTestJsonNode* input;\n")
            f.write("    const char* expected_string;\n")
            f.write("    const char* expected_hex;\n")
            f.write("} GeneratedJcsVector;\n\n")

            calls = []
            for i, vec in enumerate(all_vectors):
                dump_c_declarations(vec["input"], f"generated_jcs_input_{i}", f)
                _collect_c_init_calls(vec["input"], f"generated_jcs_input_{i}", calls)

                # Encode expected_string strictly
                encoded = vec["expected_string"].encode('utf-8')
                escaped = ''.join(f'\\x{b:02x}' for b in encoded)
                esc_str = f'"{escaped}"'

                esc_hex = json.dumps(vec["expected_hex"])

                f.write(f"static const GeneratedJcsVector generated_jcs_vector_{i} = {{\n")
                f.write(f"    {json.dumps(vec['name'])},\n")
                f.write(f"    &generated_jcs_input_{i},\n")
                f.write(f"    {esc_str},\n")
                f.write(f"    {esc_hex}\n")
                f.write("};\n\n")

            f.write(f"static const GeneratedJcsVector* const generated_jcs_vectors[{max(1, len(all_vectors))}] = {{\n")
            for i in range(len(all_vectors)):
                f.write(f"    &generated_jcs_vector_{i},\n")
            f.write("};\n\n")

            f.write(f"static const size_t generated_jcs_vectors_count = {len(all_vectors)};\n\n")

            f.write("static void generated_jcs_fixtures_init(void) {\n")
            for call in calls:
                f.write(f"    {call};\n")
            f.write("}\n\n")

            f.write("#endif\n")

    # Generate C++ header
    if cpp_out_path:
        with open(cpp_out_path, 'w', encoding='utf-8') as f:
            f.write("/* GENERATED FILE - DO NOT EDIT */\n")
            f.write("#ifndef GENERATED_JCS_POSITIVE_LOADER_FIXTURES_HPP\n")
            f.write("#define GENERATED_JCS_POSITIVE_LOADER_FIXTURES_HPP\n\n")

            f.write("struct GeneratedJcsVector {\n")
            f.write("    const char* name;\n")
            f.write("    vault::jcs::test::JsonNode* input;\n")
            f.write("    const char* expected_string;\n")
            f.write("    const char* expected_hex;\n")
            f.write("};\n\n")

            for i, vec in enumerate(all_vectors):
                dump_cpp_declarations(vec["input"], f"generated_jcs_input_{i}", f)

                encoded = vec["expected_string"].encode('utf-8')
                escaped = ''.join(f'\\x{b:02x}' for b in encoded)
                esc_str = f'"{escaped}"'

                esc_hex = json.dumps(vec["expected_hex"])

                f.write(f"static const GeneratedJcsVector generated_jcs_vector_{i} = {{\n")
                f.write(f"    {json.dumps(vec['name'])},\n")
                f.write(f"    &generated_jcs_input_{i},\n")
                f.write(f"    {esc_str},\n")
                f.write(f"    {esc_hex}\n")
                f.write("};\n\n")

            f.write(f"static const GeneratedJcsVector* const generated_jcs_vectors[{max(1, len(all_vectors))}] = {{\n")
            for i in range(len(all_vectors)):
                f.write(f"    &generated_jcs_vector_{i},\n")
            f.write("};\n\n")

            f.write(f"static const size_t generated_jcs_vectors_count = {len(all_vectors)};\n\n")

            f.write("static void generated_jcs_fixtures_init() {}\n\n")

            f.write("#endif\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--c-out', help='Path to output C header')
    parser.add_argument('--cpp-out', help='Path to output C++ header')
    parser.add_argument('inputs', nargs='+', help='Input JSON files')
    args = parser.parse_args()

    generate(args.c_out, args.cpp_out, args.inputs)

if __name__ == '__main__':
    main()
