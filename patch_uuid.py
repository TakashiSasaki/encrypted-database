import re

# Update go/internal/sqlitev1/validator.go
with open("go/internal/sqlitev1/validator.go", "r") as f:
    go_content = f.read()
go_content = go_content.replace(
    r'regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)',
    r'regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)'
)
with open("go/internal/sqlitev1/validator.go", "w") as f:
    f.write(go_content)

# Update rust/src/sqlitev1.rs
with open("rust/src/sqlitev1.rs", "r") as f:
    rust_content = f.read()
rust_content = rust_content.replace(
    r'Regex::new(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$").unwrap()',
    r'Regex::new(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$").unwrap()'
)
with open("rust/src/sqlitev1.rs", "w") as f:
    f.write(rust_content)
