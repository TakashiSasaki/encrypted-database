#include <iostream>
#include "vault.hpp"

int main() {
    std::string expected = "vault cpp smoke test ok";
    std::string actual = vault::cpp_smoke_test();
    if (actual != expected) {
        std::cerr << "Expected \"" << expected << "\", got \"" << actual << "\"" << std::endl;
        return 1;
    }
    std::cout << "Test passed." << std::endl;
    return 0;
}
