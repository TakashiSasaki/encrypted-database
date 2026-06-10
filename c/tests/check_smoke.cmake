execute_process(
    COMMAND "${EXECUTABLE}"
    RESULT_VARIABLE res
    OUTPUT_VARIABLE out
    ERROR_VARIABLE err
)

if(NOT res EQUAL 0)
    message(FATAL_ERROR "Smoke test failed. Exit code: ${res}\nStdout: ${out}\nStderr: ${err}")
endif()

# Normalize line endings to LF for a consistent exact match
string(REPLACE "\r\n" "\n" out "${out}")

if(NOT out STREQUAL EXPECTED_OUTPUT)
    message(FATAL_ERROR "Smoke test output mismatch.\nExpected: '${EXPECTED_OUTPUT}'\nGot: '${out}'")
endif()
