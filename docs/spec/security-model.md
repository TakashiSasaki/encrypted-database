# Security Model

This section outlines the threat model and the security guarantees provided by this specification.

## Scope of Protection

This specification is designed to protect confidential payloads against offline attacks and to limit the exposure of key material during active operation.

**In-Scope Defenses:**
1. **Offline Database Theft:** If the SQLite database file is stolen, the attacker cannot read the confidential payloads without also obtaining the `unlock_kek` (e.g., via a compromised passphrase, a stolen OS secret, or a compromised hardware token).
2. **Key Compromise Isolation:** Because payloads are encrypted with unique `record_dek`s, compromising a single DEK does not compromise the entire database.
3. **Context Downgrade Attacks:** The strict AAD policy binding prevents an attacker from successfully transplanting an encrypted payload from one object/record to another. The AEAD tag verification will fail upon decryption.
4. **Metadata Leakage in Identifiers:** The use of UUIDv4 for all key identifiers (`kid`) ensures that the IDs themselves do not leak metadata about key purpose, creation time, or provider.

**Out-of-Scope (Unmitigated) Threats:**
1. **Active Live Device Compromise (Malware):** If the device running the application is compromised while the database is unlocked, the attacker can extract the `database_kek` from memory or hook the decryption routines.
2. **Metadata Frequency Analysis:** Blind indexes leak the frequency of identical values in indexed fields.
3. **Traffic Analysis on Remote KMS:** If a remote KMS is used, network observers might infer activity patterns based on the timing and frequency of KMS requests.

## Material Handling and Memory Protection

The `unlock_provider_tbl.material_handling` column indicates how sensitive key material is exposed to the application's memory space:

- `derived_in_memory`: (e.g., Argon2id) The derived KEK exists briefly in application memory and must be explicitly zeroed after use.
- `exported_secret`: (e.g., OS Keychain) The secret is retrieved into application memory.
- `non_exportable_key`: (e.g., Secure Enclave, Android Keystore) The key itself never enters application memory; the application requests cryptographic operations via handles.
- `remote_unwrap`: (e.g., AWS KMS) The KEK never enters local memory. The wrapped `database_kek` is sent, and the unwrapped `database_kek` is received.

Implementers MUST ensure that any intermediate secrets (like passphrases) and unwrapped KEKs/DEKs are zeroed from memory as soon as they are no longer needed.
