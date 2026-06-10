cmake_minimum_required(VERSION 3.10)
project(vault_c C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(include)

# Library
add_library(vault_c_lib src/vault.c)

# CLI Executable
add_executable(vault_c_smoke src/main.c)
target_link_libraries(vault_c_smoke PRIVATE vault_c_lib)

# Tests
enable_testing()
add_executable(test_vault tests/test_vault.c)
target_link_libraries(test_vault PRIVATE vault_c_lib)
add_test(NAME test_vault COMMAND test_vault)

add_test(NAME test_vault_c_smoke COMMAND vault_c_smoke)
set_tests_properties(test_vault_c_smoke PROPERTIES PASS_REGULAR_EXPRESSION "vault c smoke test ok")
