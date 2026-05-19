```mermaid
erDiagram
    key_profile_tbl {
        TEXT key_class PK, FK "References key_class_tbl"
        TEXT purpose PK
        TEXT alg PK
        TEXT description
    }

    key_tbl {
        TEXT kid PK
        TEXT key_class FK "composite FK"
        TEXT purpose FK "composite FK"
        TEXT alg FK "composite FK"
        TEXT status
    }
```
