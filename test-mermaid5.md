```mermaid
erDiagram
    key_profile_tbl {
        TEXT key_class PK, FK "References key_class_tbl"
        TEXT purpose PK
        TEXT alg PK
        TEXT description
    }
```
