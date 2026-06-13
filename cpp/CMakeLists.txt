cmake_minimum_required(VERSION 3.10)
project(vault_cpp CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Generate AAD test vectors header
set(AAD_TEST_VECTORS_JSON "${CMAKE_SOURCE_DIR}/../test-vectors/aad/aad-policies-v1.json")
set(GENERATED_AAD_HEADER "${CMAKE_BINARY_DIR}/generated_aad_vectors.h")

add_custom_command(
    OUTPUT ${GENERATED_AAD_HEADER}
    COMMAND Python3::Interpreter ${CMAKE_SOURCE_DIR}/../scripts/generate_aad_test_vectors.py ${AAD_TEST_VECTORS_JSON} ${GENERATED_AAD_HEADER}
    DEPENDS ${AAD_TEST_VECTORS_JSON} ${CMAKE_SOURCE_DIR}/../scripts/generate_aad_test_vectors.py
    COMMENT "Generating AAD test vectors header"
)
add_custom_target(generate_aad_vectors DEPENDS ${GENERATED_AAD_HEADER})

# Generate JCS test vectors header
set(JCS_TEST_VECTORS_JSON "${CMAKE_SOURCE_DIR}/../test-vectors/jcs/rfc8785-basic.json")
set(GENERATED_JCS_HEADER "${CMAKE_BINARY_DIR}/generated_jcs_vectors.h")

add_custom_command(
    OUTPUT ${GENERATED_JCS_HEADER}
    COMMAND Python3::Interpreter ${CMAKE_SOURCE_DIR}/../scripts/generate_jcs_test_vectors.py ${JCS_TEST_VECTORS_JSON} ${GENERATED_JCS_HEADER}
    DEPENDS ${JCS_TEST_VECTORS_JSON} ${CMAKE_SOURCE_DIR}/../scripts/generate_jcs_test_vectors.py
    COMMENT "Generating JCS test vectors header"
)
add_custom_target(generate_jcs_vectors DEPENDS ${GENERATED_JCS_HEADER})

# Generate generic positive loader test fixtures
set(POSITIVE_FIXTURES_CPP_HEADER "${CMAKE_BINARY_DIR}/generated_jcs_positive_loader_fixtures.hpp")

add_custom_command(
    OUTPUT ${POSITIVE_FIXTURES_CPP_HEADER}
    COMMAND Python3::Interpreter ${CMAKE_SOURCE_DIR}/../scripts/generate_jcs_positive_loader_fixtures.py --cpp-out ${POSITIVE_FIXTURES_CPP_HEADER} ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/utf16-key-ordering.json ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/rfc8785-basic.json ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/generic-positive-coverage.json
    DEPENDS ${CMAKE_SOURCE_DIR}/../scripts/generate_jcs_positive_loader_fixtures.py ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/utf16-key-ordering.json ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/rfc8785-basic.json ${CMAKE_SOURCE_DIR}/../test-vectors/jcs/generic-positive-coverage.json
    COMMENT "Generating generic positive loader test fixtures for C++"
)
add_custom_target(generate_jcs_positive_loader_fixtures DEPENDS ${POSITIVE_FIXTURES_CPP_HEADER})

# Library
add_library(vault_cpp_lib src/vault.cpp src/vault_aad.cpp src/vault_uuid.cpp src/vault_content_type.cpp src/vault_jcs.cpp src/vault_jcs_model.cpp)
target_include_directories(vault_cpp_lib PRIVATE ${CMAKE_SOURCE_DIR}/../c/src)

# CLI Executable
add_executable(vault_cpp_smoke src/main.cpp)
target_link_libraries(vault_cpp_smoke PRIVATE vault_cpp_lib)

# Tests
enable_testing()
add_executable(test_vault tests/test_vault.cpp)
target_link_libraries(test_vault PRIVATE vault_cpp_lib)
add_test(NAME test_vault COMMAND test_vault)

add_executable(test_aad tests/test_aad.cpp)
target_include_directories(test_aad PRIVATE src ${CMAKE_BINARY_DIR})
target_link_libraries(test_aad PRIVATE vault_cpp_lib)
add_dependencies(test_aad generate_aad_vectors)
add_test(NAME test_aad COMMAND test_aad)

add_executable(test_uuid tests/test_uuid.cpp)
target_include_directories(test_uuid PRIVATE src)
target_link_libraries(test_uuid PRIVATE vault_cpp_lib)
add_test(NAME test_uuid COMMAND test_uuid)

add_executable(test_content_type tests/test_content_type.cpp)
target_include_directories(test_content_type PRIVATE src)
target_link_libraries(test_content_type PRIVATE vault_cpp_lib)
add_test(NAME test_content_type COMMAND test_content_type)

add_executable(test_jcs tests/test_jcs.cpp)
target_include_directories(test_jcs PRIVATE src ${CMAKE_BINARY_DIR} ${CMAKE_SOURCE_DIR}/../c/src)
target_link_libraries(test_jcs PRIVATE vault_cpp_lib)
add_dependencies(test_jcs generate_jcs_vectors)
add_test(NAME test_jcs COMMAND test_jcs)

add_executable(test_jcs_positive_vector_loader tests/test_jcs_positive_vector_loader.cpp)
target_include_directories(test_jcs_positive_vector_loader PRIVATE src ${CMAKE_BINARY_DIR})
target_link_libraries(test_jcs_positive_vector_loader PRIVATE vault_cpp_lib)
add_dependencies(test_jcs_positive_vector_loader generate_jcs_positive_loader_fixtures)
add_test(NAME test_jcs_positive_vector_loader COMMAND test_jcs_positive_vector_loader)

add_test(NAME test_vault_cpp_smoke COMMAND ${CMAKE_COMMAND} -DEXECUTABLE=$<TARGET_FILE:vault_cpp_smoke> "-DEXPECTED_OUTPUT=vault cpp smoke test ok\n" -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_smoke.cmake)

add_executable(test_jcs_model tests/test_jcs_model.cpp)
target_include_directories(test_jcs_model PRIVATE src)
target_link_libraries(test_jcs_model PRIVATE vault_cpp_lib)
add_test(NAME test_jcs_model COMMAND test_jcs_model)

add_executable(test_jcs_model_serialize tests/test_jcs_model_serialize.cpp)
target_include_directories(test_jcs_model_serialize PRIVATE src)
target_link_libraries(test_jcs_model_serialize PRIVATE vault_cpp_lib)
add_test(NAME test_jcs_model_serialize COMMAND test_jcs_model_serialize)

add_executable(test_jcs_model_vectors tests/test_jcs_model_vectors.cpp)
target_include_directories(test_jcs_model_vectors PRIVATE src ${CMAKE_BINARY_DIR} ${CMAKE_SOURCE_DIR}/../c/src)
target_link_libraries(test_jcs_model_vectors PRIVATE vault_cpp_lib)
add_dependencies(test_jcs_model_vectors generate_jcs_vectors)
add_test(NAME test_jcs_model_vectors COMMAND test_jcs_model_vectors)
