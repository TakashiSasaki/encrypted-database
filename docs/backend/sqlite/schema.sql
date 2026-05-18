CREATE TABLE IF NOT EXISTS key_class_tbl (
    key_class TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    is_wrapping_key INTEGER NOT NULL CHECK (is_wrapping_key IN (0, 1)),
    is_data_key INTEGER NOT NULL CHECK (is_data_key IN (0, 1)),
    is_active_definition INTEGER NOT NULL DEFAULT 1 CHECK (is_active_definition IN (0, 1))
);

INSERT OR IGNORE INTO key_class_tbl (key_class, description, is_wrapping_key, is_data_key) VALUES
('unlock_kek',   'Top-level unlock key-encryption key obtained from passphrase KDF, OS secure storage, Shamir recovery, KMS, or hardware token.', 1, 0),
('database_kek', 'Database-level key-encryption key for wrapping record or file data-encryption keys.', 1, 0),
('workspace_kek','Optional key-encryption key for workspace, collection, project, or sharing boundary.', 1, 0),
('record_dek',   'Data-encryption key for one logical encrypted object or record.', 0, 1),
('file_dek',     'Data-encryption key for one file or large blob.', 0, 1),
('index_key',    'Key for keyed blind indexes such as HMAC-based search indexes.', 0, 0);

CREATE TABLE IF NOT EXISTS key_profile_tbl (
    key_class TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (key_class, purpose, alg),
    FOREIGN KEY (key_class) REFERENCES key_class_tbl(key_class)
);

INSERT OR IGNORE INTO key_profile_tbl (key_class, purpose, alg, description) VALUES
('unlock_kek',   'wrap_database_keys', 'A256GCM',     'Unlock KEK used to unwrap database KEKs.'),
('database_kek', 'wrap_record_keys',   'A256GCM',     'Database KEK used to wrap record DEKs.'),
('workspace_kek','wrap_record_keys',   'A256GCM',     'Workspace KEK used for sharing or project boundaries.'),
('record_dek',   'encrypt_payload',    'A256GCM',     'Record DEK used to encrypt JSON payloads.'),
('file_dek',     'encrypt_blob',       'A256GCM',     'File DEK used to encrypt binary blobs.'),
('index_key',    'blind_index',        'HMAC-SHA256', 'Key used for deterministic keyed indexes.');

CREATE TABLE IF NOT EXISTS key_tbl (
    kid TEXT PRIMARY KEY NOT NULL CHECK (kid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    key_class TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'decrypt_only', 'disabled', 'destroyed')),
    created_at_ms INTEGER NOT NULL,
    activated_at_ms INTEGER,
    deactivated_at_ms INTEGER,
    destroyed_at_ms INTEGER,
    description_json TEXT CHECK (description_json IS NULL OR json_valid(description_json)),
    FOREIGN KEY (key_class, purpose, alg) REFERENCES key_profile_tbl(key_class, purpose, alg)
);

CREATE TABLE IF NOT EXISTS wrapped_key_tbl (
    wrap_id TEXT PRIMARY KEY NOT NULL CHECK (wrap_id GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    wrapped_kid TEXT NOT NULL CHECK (wrapped_kid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    wrapping_kid TEXT NOT NULL CHECK (wrapping_kid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    envelope_v INTEGER NOT NULL CHECK (envelope_v = 1),
    envelope_type TEXT NOT NULL CHECK (envelope_type = 'key_wrap'),
    wrap_alg TEXT NOT NULL,
    nonce BLOB NOT NULL,
    wrapped_key BLOB NOT NULL,
    aad_policy TEXT NOT NULL,
    aad_context_json TEXT NOT NULL CHECK (json_valid(aad_context_json)),
    created_at_ms INTEGER NOT NULL,
    FOREIGN KEY (wrapped_kid) REFERENCES key_tbl(kid),
    FOREIGN KEY (wrapping_kid) REFERENCES key_tbl(kid)
);

CREATE TABLE IF NOT EXISTS encrypted_object_tbl (
    object_uuid TEXT PRIMARY KEY NOT NULL CHECK (object_uuid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    envelope_v INTEGER NOT NULL CHECK (envelope_v = 1),
    envelope_type TEXT NOT NULL CHECK (envelope_type = 'aead'),
    schema_uuid TEXT NOT NULL CHECK (schema_uuid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    content_type TEXT NOT NULL,
    alg TEXT NOT NULL,
    kid TEXT NOT NULL CHECK (kid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    nonce BLOB NOT NULL,
    ciphertext BLOB NOT NULL,
    aad_policy TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    FOREIGN KEY (kid) REFERENCES key_tbl(kid)
);

CREATE TABLE IF NOT EXISTS unlock_method_tbl (
    unlock_method TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO unlock_method_tbl (unlock_method, description) VALUES
('passphrase_kdf', 'Derive an unlock KEK from a user-supplied passphrase using a password KDF.'),
('os_secret_store', 'Retrieve an exportable unlock secret from an OS-protected secret store.'),
('os_key_handle', 'Use a non-exportable OS, TEE, or secure hardware key handle to perform unwrap/decrypt.'),
('threshold_recovery', 'Reconstruct an unlock KEK from threshold shares.'),
('recovery_code_kdf', 'Derive an unlock KEK from a high-entropy recovery code or phrase.'),
('hardware_token', 'Use an external hardware authenticator, smart card, or token.'),
('remote_kms', 'Use a remote KMS or HSM service to unwrap or release key material.'),
('remote_escrow', 'Use an external escrow or delegated recovery service.'),
('test_only', 'Testing-only unlock method, never allowed in production.');

CREATE TABLE IF NOT EXISTS unlock_provider_tbl (
    unlock_provider TEXT PRIMARY KEY,
    unlock_method TEXT NOT NULL,
    config_schema_id TEXT NOT NULL,
    provider_display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    material_handling TEXT NOT NULL CHECK (
        material_handling IN (
            'derived_in_memory',
            'exported_secret',
            'non_exportable_key',
            'remote_unwrap',
            'threshold_reconstruction'
        )
    ),
    locality TEXT NOT NULL CHECK (
        locality IN ('local', 'remote', 'hybrid')
    ),
    user_presence_policy TEXT NOT NULL CHECK (
        user_presence_policy IN (
            'not_applicable',
            'not_required',
            'optional',
            'required',
            'provider_dependent'
        )
    ),
    production_status TEXT NOT NULL CHECK (
        production_status IN (
            'stable',
            'experimental',
            'planned',
            'deprecated',
            'test_only'
        )
    ),
    FOREIGN KEY (unlock_method) REFERENCES unlock_method_tbl(unlock_method)
);

INSERT OR IGNORE INTO unlock_provider_tbl (
    unlock_provider, unlock_method, config_schema_id, provider_display_name,
    description, material_handling, locality, user_presence_policy, production_status
) VALUES
('passphrase_argon2id', 'passphrase_kdf', 'passphrase_argon2id_v1', 'Passphrase + Argon2id',
 'Derives an unlock KEK from a user memorized passphrase using Argon2id.', 'derived_in_memory', 'local', 'required', 'stable');

CREATE TABLE IF NOT EXISTS platform_tbl (
    platform TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO platform_tbl (platform, description) VALUES
('windows', 'Microsoft Windows desktop environment.'),
('macos', 'Apple macOS desktop environment.'),
('linux', 'Linux desktop or server environment.'),
('android', 'Android application environment.'),
('ios', 'iOS application environment.'),
('web', 'Web browser environment.'),
('server', 'Generic server-side runtime.'),
('cloud', 'Cloud-managed runtime or external cloud service context.');

CREATE TABLE IF NOT EXISTS unlock_provider_platform_tbl (
    unlock_provider TEXT NOT NULL,
    platform TEXT NOT NULL,
    support_level TEXT NOT NULL CHECK (
        support_level IN ('native', 'supported', 'possible', 'unsupported')
    ),
    implementation_status TEXT NOT NULL CHECK (
        implementation_status IN ('implemented', 'planned', 'experimental', 'deprecated', 'unsupported')
    ),
    PRIMARY KEY (unlock_provider, platform),
    FOREIGN KEY (unlock_provider) REFERENCES unlock_provider_tbl(unlock_provider),
    FOREIGN KEY (platform) REFERENCES platform_tbl(platform)
);

INSERT OR IGNORE INTO unlock_provider_platform_tbl (unlock_provider, platform, support_level, implementation_status) VALUES
('passphrase_argon2id', 'windows', 'supported', 'implemented'),
('passphrase_argon2id', 'macos', 'supported', 'implemented'),
('passphrase_argon2id', 'linux', 'supported', 'implemented'),
('passphrase_argon2id', 'server', 'supported', 'implemented'),
('passphrase_argon2id', 'web', 'supported', 'planned'),
('passphrase_argon2id', 'android', 'supported', 'planned'),
('passphrase_argon2id', 'ios', 'supported', 'planned');

CREATE TABLE IF NOT EXISTS unlock_kek_tbl (
    kid TEXT PRIMARY KEY NOT NULL CHECK (kid GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[1-8][0-9a-f][0-9a-f][0-9a-f]-[89ab][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
    unlock_provider TEXT NOT NULL,
    provider_config_json TEXT NOT NULL CHECK (json_valid(provider_config_json)),
    device_id TEXT,
    created_on_platform TEXT NOT NULL,
    FOREIGN KEY (kid) REFERENCES key_tbl(kid),
    FOREIGN KEY (unlock_provider) REFERENCES unlock_provider_tbl(unlock_provider),
    FOREIGN KEY (created_on_platform) REFERENCES platform_tbl(platform)
);
