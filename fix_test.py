import sys

content = open("integration-tests/write-matrix/test_writer_matrix.sh").read()

search = """ elif [ "$reader" = "Node" ]; then
   local no=$(node "$DIR/read_fixture_node.js" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["not_found"])' <<<"$no")" = "True" ] || return 1
 fi
 echo "$writer -> $reader delete-notfound SUCCESS"
}"""

replace = """ elif [ "$reader" = "Node" ]; then
   local no=$(node "$DIR/read_fixture_node.js" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["not_found"])' <<<"$no")" = "True" ] || return 1
 elif [ "$reader" = "Zig" ]; then
   set +e
   local zig_out
   zig_out=$("$DIR/zig_write_matrix" read "$db" "$PASSPHRASE" "$object_uuid" 2>&1)
   local exit_code=$?
   set -e
   [[ "$zig_out" == *"Object not found"* ]] || return 1
   [ $exit_code -ne 0 ] || return 1
 fi
 echo "$writer -> $reader delete-notfound SUCCESS"
}"""

with open("integration-tests/write-matrix/test_writer_matrix.sh", "w") as f:
    f.write(content.replace(search, replace))
