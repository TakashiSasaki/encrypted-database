# Provider and Platform Model

The unlock capability of a database is modeled by the relationships between abstract unlock methods, concrete unlock providers, and the physical platforms they run on.

## Abstract Methods vs Concrete Providers

- **Unlock Method:** An abstract cryptographic or architectural approach to unlocking the database. For example: `passphrase_kdf`, `os_secret_store`, `remote_kms`.
- **Unlock Provider:** A specific implementation of an unlock method. For example, `passphrase_argon2id` is a concrete provider implementing the `passphrase_kdf` method.
- **Provider Platform Binding:** The specific OS or runtime environment a provider instance is bound to.

## Platform Constraints and Prohibitions

Every unlock provider instance MUST record a concrete platform name in `unlock_kek_tbl.created_on_platform`. This value MUST reference `platform_tbl(platform)`.

**Important Rule:** The value `cross_platform` or an empty/null string is **PROHIBITED**.

### Rationale against `cross_platform`
`cross_platform` is ambiguous. It can mean algorithm portability, a test environment, no platform binding, an unspecified platform, or an unsupported deployment. These meanings must not be conflated.

A provider that is conceptually portable, such as `passphrase_argon2id`, MUST be represented by explicit provider-platform rows:

```text
(passphrase_argon2id, windows)
(passphrase_argon2id, macos)
(passphrase_argon2id, linux)
(passphrase_argon2id, server)
(passphrase_argon2id, web)
(passphrase_argon2id, android)
(passphrase_argon2id, ios)
```

The fact that the algorithm is portable is expressed by repeated concrete mappings, not by an abstract platform label. Test environments MUST use concrete platform strings (e.g., `"linux"`).
