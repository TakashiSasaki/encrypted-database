cmake_minimum_required(VERSION 3.10)
project(vault_cpp CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# Library
add_library(vault_cpp_lib src/vault.cpp)

# CLI Executable
add_executable(vault_cpp_smoke src/main.cpp)
target_link_libraries(vault_cpp_smoke PRIVATE vault_cpp_lib)

# Tests
enable_testing()
add_executable(test_vault tests/test_vault.cpp)
target_link_libraries(test_vault PRIVATE vault_cpp_lib)
add_test(NAME test_vault COMMAND test_vault)

add_test(NAME test_vault_cpp_smoke COMMAND vault_cpp_smoke)
set_tests_properties(test_vault_cpp_smoke PROPERTIES PASS_REGULAR_EXPRESSION "vault cpp smoke test ok")
