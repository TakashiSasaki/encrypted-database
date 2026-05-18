# Operational Scenarios

This document outlines the standard operational flows for interacting with the encrypted database.

## 1. Creating a New Database

1. Generate a new `database_kek` using a Cryptographically Secure Pseudo-Random Number Generator (CSPRNG).
2. Register the `database_kek` in the `key_tbl`.
3. Create at least one `unlock_kek` pathway (e.g., derive from a user password using Argon2id).
4. Register the `unlock_kek` in the `key_tbl` and its provider configuration in `unlock_kek_tbl`.
5. Wrap the `database_kek` using the `unlock_kek`.
6. Store the wrapped `database_kek` in `wrapped_key_tbl`.
7. (Optional) Add additional unlock pathways like biometric OS secret store or Shamir recovery by wrapping the same `database_kek` with new `unlock_kek`s.

## 2. Unlocking the Database

1. Receive input from the user or OS (e.g., a passphrase).
2. Look up the corresponding active `unlock_kek` and its configuration.
3. Derive or retrieve the `unlock_kek` bytes.
4. Retrieve the wrapped `database_kek` from `wrapped_key_tbl`.
5. Unwrap the `database_kek` using the `unlock_kek` and the appropriate AAD policy context.
6. Hold the `database_kek` in memory as the active database key.

## 3. Storing an Encrypted Payload

1. Ensure the database is unlocked (active `database_kek` is in memory).
2. Generate a new `record_dek` via CSPRNG.
3. Register the `record_dek` in the `key_tbl`.
4. Wrap the `record_dek` using the `database_kek`.
5. Store the wrapped `record_dek` in `wrapped_key_tbl`.
6. Encrypt the target JSON payload using the `record_dek` and the `record-payload-v1` AAD policy.
7. Store the encrypted envelope (ciphertext, nonce, metadata) in `encrypted_object_tbl`.

## 4. Retrieving an Encrypted Payload

1. Ensure the database is unlocked.
2. Retrieve the envelope from `encrypted_object_tbl` using the object's UUID.
3. Look up the corresponding wrapped `record_dek` in `wrapped_key_tbl`.
4. Unwrap the `record_dek` using the active `database_kek`.
5. Decrypt the envelope's ciphertext using the `record_dek` and the verified AAD policy context.
6. Return the plaintext JSON payload.
