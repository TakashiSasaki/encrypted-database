> **Archived Note:** This document is the original integrated draft specification and is kept here for historical reference. Please refer to the split, updated documentation under `docs/spec/`, `docs/backend/`, and `docs/providers/` for current and authoritative information.

# 暗号化保存ライブラリ 鍵管理・保存仕様ドラフト

## 1. 目的

本仕様は、SQLite などのローカル永続化層に秘匿対象データを保存するアプリケーション向けに、アプリケーション層暗号化、鍵階層、鍵ラッピング、アンロック手段、復旧経路、検索用補助鍵を統一的に扱うための設計を定義する。

設計上の中心方針は、データベースファイル全体の暗号化だけに依存せず、秘匿対象 payload をアプリケーション層で暗号化済み envelope として保存し、検索・同期・整合性管理に必要な非秘密メタデータだけを平文カラムとして保持することである。

Bitwarden のように、機密フィールドを暗号化済み表現として扱い、ID・日時・種別・同期用メタデータは分離して保持する考え方を参考にする。ただし、Bitwarden 固有の `EncString` 形式をそのまま採用するのではなく、AEAD を前提とする独自の versioned envelope を採用する。

## 2. 設計原則

1. 平文の秘密値、平文鍵、マスターパスワード、Shamir share、復旧コードは SQLite に保存しない。

2. 秘匿対象 payload は、`record_dek` または `file_dek` で AEAD 暗号化する。

3. payload 暗号化鍵である `record_dek` / `file_dek` は、上位鍵で wrap して保存する。

4. 鍵階層の入口は `unlock_kek` と呼ぶ。`unlock_kek` は、パスフレーズ KDF、OS secret store、OS key handle、Shamir recovery、hardware token、remote KMS など複数の unlock provider から得られる。

5. `unlock_kek` は単一である必要はない。同じ `database_kek` を複数の `unlock_kek` で wrap してよい。

6. `unlock_method` は抽象分類、`unlock_provider` は具体実装、`unlock_kek_tbl` は個別インスタンス設定を表す。

7. `provider_config_json` には provider 固有の非秘密設定だけを入れる。`provider`, `method`, `platform` のようなマスタ側に存在する値は重複保存しない。

8. AEAD の AAD は、暗号文を保存文脈に束縛するために使う。実 AAD byte sequence はライブラリ内部で決定論的に生成し、envelope や DB には `aad_policy` を保存する。

9. Base64URL や BLOB の保存形式は利用層に応じて選ぶ。DB 内部では BLOB カラム、API / ファイル交換では JSON envelope を推奨する。

10. SQLite に保存する JSON、AAD の生成に使う JSON、署名・MAC・ハッシュ・UUID 生成などの入力になる JSON は、常に正規化する。正規化方式は JCS 相当の canonical JSON を標準とし、厳密な相互運用が必要な場合は RFC 8785 対応実装を使う。正規化対象外の自由形式 JSON を保存しない。

## 3. 用語

### 3.0 識別子と JSON 正規化の基本方針

`kid` は UUIDv4 文字列とする。人間可読な接頭辞、鍵種別、作成日、provider 名、用途名などを `kid` に埋め込まない。鍵の種別、用途、表示名、作成時刻、provider、platform、状態は、それぞれ `key_class`, `purpose`, `description_json`, `created_at_ms`, `unlock_provider`, `platform`, `status` などのカラムで表す。

UUIDv4 を採用する理由は、`kid` を意味のない安定識別子にし、命名変更や分類変更の影響を避けるためである。UUIDv7 や UUIDv8 は時刻や独自 layout を含められる利点があるが、鍵 ID では時刻情報や意味情報を ID 自体に含める必要性が低く、むしろメタデータ漏洩を避けるため UUIDv4 を標準とする。

本仕様で保存する JSON は常に正規化する。対象には `description_json`, `aad_context_json`, `provider_config_json`, 暗号化前の JSON payload、blind index 入力用の正規化値、将来の署名・MAC・ハッシュ対象 JSON を含む。JSON の意味的同一性と byte sequence の同一性を一致させることで、AAD、HMAC、UUID 生成、差分同期、テスト再現性の不整合を減らす。



### 3.1 KEK と DEK

`KEK` は Key Encryption Key であり、他の鍵を wrap / unwrap するための鍵である。`DEK` は Data Encryption Key であり、payload や blob などの実データを暗号化するための鍵である。

本仕様では以下の key class を使う。

| key_class | 意味 |
|---|---|
| `unlock_kek` | 鍵階層の入口となる KEK。パスフレーズ KDF、OS secret store、Shamir recovery などから得られる。 |
| `database_kek` | 1 つの database / vault に対応する KEK。`record_dek` や `file_dek` を wrap する。 |
| `workspace_kek` | workspace / collection / project / sharing boundary 用の任意の中間 KEK。共有境界が必要な場合に使う。 |
| `record_dek` | 1 つの論理レコード、JSON object、secret item などを暗号化する DEK。 |
| `file_dek` | 添付ファイル、大容量 BLOB、外部ファイルなどを暗号化する DEK。 |
| `index_key` | blind index、HMAC 検索インデックス、重複検出用 keyed digest などに使う鍵。 |

### 3.2 unlock_kek

`unlock_kek` は、DB 内の wrap graph において親を持たない入口鍵である。`root_kek` という名称は、単一の絶対的な根鍵を連想させるため、本仕様では `unlock_kek` と呼ぶ。

`unlock_kek` の例は以下である。

```text
master password + Argon2id → password-derived unlock_kek
OS secret store            → OS-protected unlock_kek
OS key handle              → non-exportable unlock operation
Shamir shares              → reconstructed recovery unlock_kek
Cloud KMS                  → remote unwrap capability
Hardware token             → token-mediated unwrap capability
```

マスターパスワードそのものは鍵ではない。マスターパスワードから KDF により導出された鍵が `unlock_kek` である。Shamir share そのものも鍵ではない。しきい値以上の share から復元された鍵が `unlock_kek` または recovery 用 unlock material である。

### 3.3 unlock_method / unlock_provider / unlock_kek instance

`unlock_method` は抽象的な方式分類である。OS API 名ではない。

`unlock_provider` は具体的な実装手段である。

`unlock_kek_tbl` は、実際に登録された unlock 経路の個別インスタンスである。

```text
unlock_method        = 抽象方式分類
unlock_provider      = 具体実装・API・サービス
unlock_kek instance  = 実際に登録された個別 unlock 経路
```

例:

```text
unlock_method: os_secret_store
  providers:
    windows_dpapi_user
    windows_credential_manager
    macos_keychain_generic_password
    ios_keychain_generic_password
    linux_secret_service

unlock_method: os_key_handle
  providers:
    android_keystore_key
    macos_secure_enclave_key
    ios_secure_enclave_key
    windows_cng_ncrypt_key

unlock_method: passphrase_kdf
  providers:
    passphrase_argon2id
    passphrase_pbkdf2_legacy

unlock_method: threshold_recovery
  providers:
    shamir_ssss
    shamir_slip39

unlock_method: hardware_token
  providers:
    piv_smartcard
    pkcs11_token
    openpgp_card
    fido2_prf

unlock_method: remote_kms
  providers:
    aws_kms
    gcp_cloud_kms
    azure_key_vault
```

## 4. 鍵階層

標準の鍵階層は次の 3 層である。

```text
unlock_kek
  ↓ unwraps
database_kek
  ↓ unwraps
record_dek / file_dek
  ↓ encrypts
payload / blob
```

共有境界やプロジェクト境界が必要な場合は `workspace_kek` を挟む。

```text
unlock_kek
  ↓ unwraps
database_kek
  ↓ unwraps
workspace_kek
  ↓ unwraps
record_dek / file_dek
  ↓ encrypts
payload / blob
```

ただし、最初の実装では `workspace_kek` は任意でよい。共有や権限境界がない単一ユーザー・単一 DB の場合は、`unlock_kek → database_kek → record_dek` で十分である。

### 4.1 複数 unlock 経路

同じ `database_kek` は、複数の `unlock_kek` で wrap できる。

```text
database_kek wrapped by passphrase_argon2id unlock_kek
database_kek wrapped by os_secret_store unlock_kek
database_kek wrapped by shamir_recovery unlock_kek
```

これにより、通常利用では OS 保護経路を使い、移行・復旧ではマスターパスワード経路や Shamir 経路を使える。

### 4.2 Shamir recovery の位置づけ

Shamir secret sharing は、通常運用の復号経路に常時入れない。復旧用 `unlock_kek` または recovery unlock material を復元するための補助機構として扱う。

推奨構造:

```text
通常運用:
  passphrase_kdf / os_secret_store / os_key_handle
    → unwrap database_kek
    → unwrap record_dek
    → decrypt payload

復旧運用:
  Shamir shares, e.g. 3-of-5
    → reconstruct recovery unlock_kek
    → unwrap database_kek
    → unwrap record_dek
    → decrypt payload
```

各 record DEK を Shamir で分割する設計は避ける。レコード数が増えると share 管理が破綻しやすい。

## 5. 暗号 envelope

payload 暗号化 envelope の JSON 表現は以下を標準とする。

```json
{
  "v": 1,
  "type": "aead",
  "alg": "A256GCM",
  "kid": "dek-...",
  "nonce": "base64url...",
  "ct": "base64url...",
  "aad_policy": "record-payload-v1"
}
```

### 5.1 フィールド

| フィールド | 意味 |
|---|---|
| `v` | envelope format のバージョン。 |
| `type` | envelope の種類。payload 暗号文なら `aead`。 |
| `alg` | 暗号アルゴリズム。初期標準は `A256GCM`。 |
| `kid` | 復号に必要な鍵 ID。payload の場合は `record_dek` または `file_dek` を指す。 |
| `nonce` | AEAD nonce。AES-GCM では通常 96 bit。公開値として暗号文と一緒に保存する。 |
| `ct` | 暗号文。AES-GCM の場合、ciphertext と authentication tag を結合した値として扱ってよい。 |
| `aad_policy` | AAD の生成規則名。実 AAD 本体ではない。 |

### 5.2 nonce と IV

AEAD における `nonce` は、従来の用語でいう IV に相当する。ただし、`nonce` は “number used once” の意味を持ち、同一鍵のもとで再利用してはいけないという性質を強調する。

AES-GCM では、同じ鍵と同じ nonce を再利用してはならない。標準的には 12 byte のランダム nonce を CSPRNG で生成する。

### 5.3 AAD

AAD は暗号化されないが、改ざん検出の対象になる追加認証データである。

本仕様では、AAD に以下のような非秘密文脈を含めることを推奨する。

```json
{
  "v": 1,
  "aad_policy": "record-payload-v1",
  "object_uuid": "...",
  "schema_uuid": "...",
  "content_type": "...",
  "kid": "...",
  "alg": "A256GCM"
}
```

暗号文を別 object、別 schema、別 field に移植した場合、AAD 検証が失敗するようにする。

AAD には秘密情報を入れてはならない。AAD は認証されるが暗号化されない。

## 6. SQLite スキーマ

### 6.1 key_class_tbl

鍵クラスのマスタ。

```sql
CREATE TABLE key_class_tbl (
    key_class TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    is_wrapping_key INTEGER NOT NULL CHECK (is_wrapping_key IN (0, 1)),
    is_data_key INTEGER NOT NULL CHECK (is_data_key IN (0, 1)),
    is_active_definition INTEGER NOT NULL DEFAULT 1 CHECK (is_active_definition IN (0, 1))
);
```

初期値:

```sql
INSERT INTO key_class_tbl (
    key_class,
    description,
    is_wrapping_key,
    is_data_key
) VALUES
('unlock_kek',   'Top-level unlock key-encryption key obtained from passphrase KDF, OS secure storage, Shamir recovery, KMS, or hardware token.', 1, 0),
('database_kek', 'Database-level key-encryption key for wrapping record or file data-encryption keys.', 1, 0),
('workspace_kek','Optional key-encryption key for workspace, collection, project, or sharing boundary.', 1, 0),
('record_dek',   'Data-encryption key for one logical encrypted object or record.', 0, 1),
('file_dek',     'Data-encryption key for one file or large blob.', 0, 1),
('index_key',    'Key for keyed blind indexes such as HMAC-based search indexes.', 0, 0);
```

### 6.2 key_profile_tbl

`key_class + purpose + alg` の許可組み合わせを定義する。

```sql
CREATE TABLE key_profile_tbl (
    key_class TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (key_class, purpose, alg),
    FOREIGN KEY (key_class) REFERENCES key_class_tbl(key_class)
);
```

初期値:

```sql
INSERT INTO key_profile_tbl (
    key_class,
    purpose,
    alg,
    description
) VALUES
('unlock_kek',   'wrap_database_keys', 'A256GCM',     'Unlock KEK used to unwrap database KEKs.'),
('database_kek', 'wrap_record_keys',   'A256GCM',     'Database KEK used to wrap record DEKs.'),
('workspace_kek','wrap_record_keys',   'A256GCM',     'Workspace KEK used for sharing or project boundaries.'),
('record_dek',   'encrypt_payload',    'A256GCM',     'Record DEK used to encrypt JSON payloads.'),
('file_dek',     'encrypt_blob',       'A256GCM',     'File DEK used to encrypt binary blobs.'),
('index_key',    'blind_index',        'HMAC-SHA256', 'Key used for deterministic keyed indexes.');
```

### 6.3 key_tbl

鍵 ID と鍵メタデータの台帳。平文鍵は保存しない。

```sql
CREATE TABLE key_tbl (
    kid TEXT PRIMARY KEY,
    key_class TEXT NOT NULL,
    purpose TEXT NOT NULL,
    alg TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'decrypt_only', 'disabled', 'destroyed')),
    created_at_ms INTEGER NOT NULL,
    activated_at_ms INTEGER,
    deactivated_at_ms INTEGER,
    destroyed_at_ms INTEGER,
    description_json TEXT CHECK (description_json IS NULL OR json_valid(description_json)),
    FOREIGN KEY (key_class, purpose, alg)
        REFERENCES key_profile_tbl(key_class, purpose, alg)
);
```

例:

```sql
INSERT INTO key_tbl (
    kid,
    key_class,
    purpose,
    alg,
    status,
    created_at_ms,
    description_json
) VALUES
(
    'ulk-passphrase-argon2id-01',
    'unlock_kek',
    'wrap_database_keys',
    'A256GCM',
    'active',
    1778947200000,
    '{"label":"Primary passphrase unlock KEK"}'
),
(
    'dbk-01972f2e-4b51-7a11-8a2f-8a4f0db0a101',
    'database_kek',
    'wrap_record_keys',
    'A256GCM',
    'active',
    1778947201000,
    '{"database_uuid":"5c9fe176-1e02-4c03-b003-d0580609cc1b"}'
),
(
    'dek-01972f3b-77c8-7a8d-b9a7-2eac8f2d9912',
    'record_dek',
    'encrypt_payload',
    'A256GCM',
    'active',
    1778947202000,
    '{"object_uuid":"01972f3b-77c8-7a8d-b9a7-2eac8f2d9912"}'
);
```

### 6.4 wrapped_key_tbl

鍵材料の wrap 済み表現を保存する。平文鍵は保存しない。

```sql
CREATE TABLE wrapped_key_tbl (
    wrapped_kid TEXT NOT NULL,
    wrapping_kid TEXT NOT NULL,
    wrap_alg TEXT NOT NULL,
    nonce BLOB NOT NULL,
    wrapped_key BLOB NOT NULL,
    aad_context_json TEXT NOT NULL CHECK (json_valid(aad_context_json)),
    created_at_ms INTEGER NOT NULL,
    PRIMARY KEY (wrapped_kid, wrapping_kid),
    FOREIGN KEY (wrapped_kid) REFERENCES key_tbl(kid),
    FOREIGN KEY (wrapping_kid) REFERENCES key_tbl(kid)
);
```

例:

```sql
INSERT INTO wrapped_key_tbl (
    wrapped_kid,
    wrapping_kid,
    wrap_alg,
    nonce,
    wrapped_key,
    aad_context_json,
    created_at_ms
) VALUES
(
    'dbk-01972f2e-4b51-7a11-8a2f-8a4f0db0a101',
    'ulk-passphrase-argon2id-01',
    'A256GCM',
    X'8F2A1C7D3E4B901122334455',
    X'F4B62A8C99D0E1A23C44556677889900AABBCCDDEEFF00112233445566778899A1B2C3D4E5F60718293A4B5C6D7E8F90',
    '{"v":1,"aad_policy":"wrap-database-key-v1","wrapped_kid":"dbk-01972f2e-4b51-7a11-8a2f-8a4f0db0a101","wrapping_kid":"ulk-passphrase-argon2id-01"}',
    1778947203000
);
```

### 6.5 encrypted_object_tbl

暗号化された payload 本体を保存する。

```sql
CREATE TABLE encrypted_object_tbl (
    object_uuid TEXT PRIMARY KEY,
    schema_uuid TEXT NOT NULL,
    content_type TEXT NOT NULL,
    alg TEXT NOT NULL,
    kid TEXT NOT NULL,
    nonce BLOB NOT NULL,
    ciphertext BLOB NOT NULL,
    aad_policy TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    FOREIGN KEY (kid) REFERENCES key_tbl(kid)
);
```

例:

```sql
INSERT INTO encrypted_object_tbl (
    object_uuid,
    schema_uuid,
    content_type,
    alg,
    kid,
    nonce,
    ciphertext,
    aad_policy,
    created_at_ms,
    updated_at_ms
) VALUES (
    '01972f3b-77c8-7a8d-b9a7-2eac8f2d9912',
    '7f9152a0-1c20-4a72-8e8e-9edc6dfc8a90',
    'application/json; profile="https://example.invalid/schema/secret-note-v1"',
    'A256GCM',
    'dek-01972f3b-77c8-7a8d-b9a7-2eac8f2d9912',
    X'CAFEBABE0011223344556677',
    X'7B4F12AA0D91C7E5A1884A0FBB23CC44D955AA66EE7700112233445566778899AABBCCDDEEFF00112233445566778899',
    'record-payload-v1',
    1778947205000,
    1778947205000
);
```

## 7. unlock method / provider / platform

### 7.1 unlock_method_tbl

抽象方式分類を表す。

```sql
CREATE TABLE unlock_method_tbl (
    unlock_method TEXT PRIMARY KEY,
    description TEXT NOT NULL
);
```

初期値:

```sql
INSERT INTO unlock_method_tbl (
    unlock_method,
    description
) VALUES
('passphrase_kdf', 'Derive an unlock KEK from a user-supplied passphrase using a password KDF.'),
('os_secret_store', 'Retrieve an exportable unlock secret from an OS-protected secret store.'),
('os_key_handle', 'Use a non-exportable OS, TEE, or secure hardware key handle to perform unwrap/decrypt.'),
('threshold_recovery', 'Reconstruct an unlock KEK from threshold shares.'),
('recovery_code_kdf', 'Derive an unlock KEK from a high-entropy recovery code or phrase.'),
('hardware_token', 'Use an external hardware authenticator, smart card, or token.'),
('remote_kms', 'Use a remote KMS or HSM service to unwrap or release key material.'),
('remote_escrow', 'Use an external escrow or delegated recovery service.'),
('test_only', 'Testing-only unlock method, never allowed in production.');
```

### 7.2 os_secret_store と os_key_handle の違い

`os_secret_store` は、OS が保護している秘密値をアプリケーションが取り出し、その secret を使って `database_kek` を unwrap する方式である。

```text
OS secret store
  stores encrypted/exportable unlock secret
        ↓ read by application
application memory
  unlock_kek bytes
        ↓ AES-GCM unwrap
database_kek
```

`os_key_handle` は、鍵素材をアプリケーションに取り出さず、OS、TEE、Secure Enclave、Android Keystore、TPM などの内部に保持された鍵ハンドルに unwrap / decrypt を依頼する方式である。

```text
OS / TEE / Secure Enclave / Keystore
  holds non-exportable key
        ↓ unwrap operation requested by app
database_kek
```

比較:

| 観点 | os_secret_store | os_key_handle |
|---|---|---|
| 鍵素材 | アプリメモリに出る | 原則アプリメモリに出ない |
| OS の役割 | secret の保存・復号・アクセス制御 | 鍵の保持と暗号操作の実行 |
| アプリの役割 | 取り出した secret で unwrap する | 鍵ハンドルに unwrap/decrypt を依頼する |
| 典型例 | DPAPI 保護 secret、Keychain generic password、Secret Service | Android Keystore key、Secure Enclave key、TPM/CNG non-exportable key |
| 実装 | 比較的単純 | API 差が大きく複雑 |
| メモリ漏洩耐性 | 弱め | 強くできる |
| 可搬性 | 比較的扱いやすい | デバイス依存が強い |

### 7.3 unlock_provider_tbl

具体 provider の性質を表す。platform は直接持たせず、多対多テーブルに分離する。

```sql
CREATE TABLE unlock_provider_tbl (
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
```

例:

```sql
INSERT INTO unlock_provider_tbl (
    unlock_provider,
    unlock_method,
    config_schema_id,
    provider_display_name,
    description,
    material_handling,
    locality,
    user_presence_policy,
    production_status
) VALUES
(
    'passphrase_argon2id',
    'passphrase_kdf',
    'passphrase_argon2id_v1',
    'Passphrase + Argon2id',
    'Derives an unlock KEK from a user memorized passphrase using Argon2id.',
    'derived_in_memory',
    'local',
    'required',
    'stable'
),
(
    'windows_dpapi_user',
    'os_secret_store',
    'windows_dpapi_user_v1',
    'Windows DPAPI Current User',
    'Stores or protects an unlock secret under the current Windows user profile.',
    'exported_secret',
    'local',
    'not_required',
    'stable'
),
(
    'macos_keychain_generic_password',
    'os_secret_store',
    'macos_keychain_generic_password_v1',
    'macOS Keychain Generic Password',
    'Stores an unlock secret as a macOS Keychain generic password item.',
    'exported_secret',
    'local',
    'provider_dependent',
    'stable'
),
(
    'android_keystore_key',
    'os_key_handle',
    'android_keystore_key_v1',
    'Android Keystore Key',
    'Uses an Android Keystore managed key, possibly hardware-backed and user-authentication-bound.',
    'non_exportable_key',
    'local',
    'provider_dependent',
    'stable'
),
(
    'shamir_ssss',
    'threshold_recovery',
    'shamir_ssss_v1',
    'Shamir Secret Sharing',
    'Reconstructs a recovery unlock KEK from threshold shares.',
    'threshold_reconstruction',
    'local',
    'required',
    'stable'
),
(
    'aws_kms',
    'remote_kms',
    'aws_kms_v1',
    'AWS KMS',
    'Uses AWS KMS to unwrap or release key material under KMS policy.',
    'remote_unwrap',
    'remote',
    'provider_dependent',
    'stable'
),
(
    'test_static',
    'test_only',
    'test_static_v1',
    'Static Test Key',
    'Testing-only provider. Must never be used in production.',
    'exported_secret',
    'local',
    'not_required',
    'test_only'
);
```

### 7.4 platform_tbl と unlock_provider_platform_tbl

provider と platform の関係は多対多である。

```sql
CREATE TABLE platform_tbl (
    platform TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE unlock_provider_platform_tbl (
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
```

例:

```sql
INSERT INTO platform_tbl (
    platform,
    description
) VALUES
('windows', 'Microsoft Windows desktop environment.'),
('macos', 'Apple macOS desktop environment.'),
('linux', 'Linux desktop or server environment.'),
('android', 'Android application environment.'),
('ios', 'iOS application environment.'),
('web', 'Web browser environment.'),
('server', 'Generic server-side runtime.'),
('cloud', 'Cloud-managed runtime or external cloud service context.');
```

```sql
INSERT INTO unlock_provider_platform_tbl (
    unlock_provider,
    platform,
    support_level,
    implementation_status
) VALUES
('windows_dpapi_user', 'windows', 'native', 'implemented'),
('macos_keychain_generic_password', 'macos', 'native', 'implemented'),
('android_keystore_key', 'android', 'native', 'implemented'),
('passphrase_argon2id', 'windows', 'supported', 'implemented'),
('passphrase_argon2id', 'macos', 'supported', 'implemented'),
('passphrase_argon2id', 'linux', 'supported', 'implemented'),
('passphrase_argon2id', 'android', 'supported', 'planned'),
('passphrase_argon2id', 'ios', 'supported', 'planned'),
('shamir_ssss', 'windows', 'supported', 'implemented'),
('shamir_ssss', 'macos', 'supported', 'implemented'),
('shamir_ssss', 'linux', 'supported', 'implemented'),
('aws_kms', 'server', 'supported', 'implemented'),
('aws_kms', 'windows', 'supported', 'planned'),
('aws_kms', 'macos', 'supported', 'planned'),
('aws_kms', 'linux', 'supported', 'planned');
```

### 7.5 unlock_kek_tbl

実際に登録された unlock KEK インスタンスを表す。`unlock_method` は置かない。`unlock_method` は `unlock_provider_tbl` から導出する。

```sql
CREATE TABLE unlock_kek_tbl (
    kid TEXT PRIMARY KEY,
    unlock_provider TEXT NOT NULL,
    provider_config_json TEXT NOT NULL CHECK (json_valid(provider_config_json)),
    device_id TEXT,
    created_on_platform TEXT,
    FOREIGN KEY (kid) REFERENCES key_tbl(kid),
    FOREIGN KEY (unlock_provider) REFERENCES unlock_provider_tbl(unlock_provider),
    FOREIGN KEY (created_on_platform) REFERENCES platform_tbl(platform)
);
```

例:

```sql
INSERT INTO unlock_kek_tbl (
    kid,
    unlock_provider,
    provider_config_json,
    device_id,
    created_on_platform
) VALUES
(
    'ulk-passphrase-argon2id-01',
    'passphrase_argon2id',
    '{"salt":"base64url...","memory_kib":262144,"iterations":3,"parallelism":4}',
    NULL,
    'windows'
),
(
    'ulk-windows-dpapi-user-01',
    'windows_dpapi_user',
    '{"scope":"current_user","secret_name":"com.example.app.ulk-windows-dpapi-user-01"}',
    'device-001',
    'windows'
),
(
    'ulk-macos-keychain-01',
    'macos_keychain_generic_password',
    '{"service":"com.example.app","account":"ulk-macos-keychain-01"}',
    'device-002',
    'macos'
),
(
    'ulk-shamir-3of5-01',
    'shamir_ssss',
    '{"threshold":3,"share_count":5,"share_set_id":"recovery-2026-05"}',
    NULL,
    'windows'
);
```

`provider_config_json` には `unlock_provider`, `unlock_method`, `platform` を入れない。これらは別カラムまたは参照テーブルから分かるため、重複保存すると矛盾が発生する。

## 8. プラットフォーム分類

`platform` は、unlock provider が動作する実行環境または利用文脈を表す。OS 名だけではなく、ブラウザ、サーバ、クラウド実行環境なども含める。

`platform` は provider の本質的属性ではない。たとえば `windows_dpapi_user` は Windows 専用だが、`passphrase_argon2id` は複数 platform で使える。したがって、`unlock_provider_tbl` に `platform` を直接持たせず、`unlock_provider_platform_tbl` で provider と platform の多対多関係を表す。

### 8.1 標準 platform 候補

| platform | 意味 | 典型的な unlock provider |
|---|---|---|
| `windows` | Windows デスクトップまたは Windows サービス環境。 | `windows_dpapi_user`, `windows_dpapi_machine`, `windows_credential_manager`, `windows_cng_ncrypt_key`, `passphrase_argon2id` |
| `macos` | macOS デスクトップアプリ環境。 | `macos_keychain_generic_password`, `macos_keychain_access_control`, `macos_secure_enclave_key`, `passphrase_argon2id` |
| `linux` | Linux デスクトップまたはサーバ環境。 | `linux_secret_service`, `linux_kwallet`, `linux_gnome_keyring`, `pkcs11_token`, `passphrase_argon2id` |
| `android` | Android アプリ環境。 | `android_keystore_key`, `android_keystore_biometric_bound_key`, `passphrase_argon2id` |
| `ios` | iOS アプリ環境。 | `ios_keychain_generic_password`, `ios_keychain_access_control`, `ios_secure_enclave_key`, `passphrase_argon2id` |
| `web` | Web ブラウザ環境。ローカル OS secret store へのアクセスは通常制限される。 | `passphrase_argon2id`, `webcrypto_derived_key`, 将来的な `webauthn_prf` |
| `server` | 汎用サーバサイド実行環境。OS は別に存在するが、運用上サーバとして扱う。 | `passphrase_argon2id`, `cloud_kms`, `pkcs11_token`, `linux_secret_service` |
| `cloud` | クラウド管理実行環境または cloud KMS の文脈。 | `aws_kms`, `gcp_cloud_kms`, `azure_key_vault` |
| `cross_platform` | 実装上 OS に強く依存しない方式を説明するための抽象 platform。原則として対応関係の便宜用であり、実運用では具体 platform に展開する。 | `passphrase_argon2id`, `shamir_ssss` |

`cross_platform` は便利だが、実装状態や動作保証を曖昧にしやすい。実際のサポート管理では、`cross_platform` だけで済ませず、`windows`, `macos`, `linux`, `android`, `ios`, `server` などへ個別に展開する方がよい。

### 8.2 support_level と implementation_status

`unlock_provider_platform_tbl` では、provider と platform の関係を二つの観点で分ける。

`support_level` は、その platform における provider の性質を表す。

| support_level | 意味 |
|---|---|
| `native` | OS や platform の標準機能として自然に利用できる。例: Windows の DPAPI、macOS Keychain、Android Keystore。 |
| `supported` | 標準機能ではないが、通常のライブラリや実装により十分に利用できる。例: Argon2id、Shamir。 |
| `possible` | 技術的には可能だが、環境依存・デバイス依存・追加ドライバ依存が強い。例: PKCS#11 token のモバイル利用。 |
| `unsupported` | 設計上または実装上、その platform では扱わない。 |

`implementation_status` は、当該アプリケーションまたはライブラリでの実装状態を表す。

| implementation_status | 意味 |
|---|---|
| `implemented` | 実装済みで通常利用できる。 |
| `planned` | 設計上予定しているが未実装。 |
| `experimental` | 実験的実装であり、互換性や安全性ポリシーがまだ固定されていない。 |
| `deprecated` | 既存データの復号互換性のために残すが、新規利用は避ける。 |
| `unsupported` | 実装しない、または明示的に無効化する。 |

この分離により、「その platform で原理的に使えるか」と「自分のライブラリで実装済みか」を区別できる。

### 8.3 platform ごとの設計上の注意

Windows では、`os_secret_store` として DPAPI current-user scope や Credential Manager が候補になる。サービス用途では machine scope もあり得るが、ユーザー分離が弱くなる可能性があるため、通常のユーザーアプリでは current-user scope を優先する。

macOS では、Keychain generic password は `os_secret_store` に対応する。Secure Enclave や Keychain 上の非抽出秘密鍵に処理を依頼する場合は `os_key_handle` に分類する。

Linux では、Secret Service、GNOME Keyring、KWallet などが候補になる。ただしデスクトップ環境、セッション、headless server で利用可能性が変わる。サーバ用途では cloud KMS や passphrase KDF の方が安定する場合がある。

Android では、Android Keystore が主要候補である。鍵本体を取り出せない非抽出鍵として扱う場合は `os_key_handle` である。生体認証は unlock method ではなく、Keystore key へのアクセス制御条件として扱う。

iOS では、Keychain generic password が `os_secret_store`、Secure Enclave key が `os_key_handle` に対応する。端末移行やバックアップ復元可否は Keychain item の accessibility 設定に依存するため、provider_config の schema で明示する必要がある。

Web では、OS secret store への直接アクセスは通常できない。基本は `passphrase_kdf`、WebCrypto による鍵導出、将来的には WebAuthn PRF / hmac-secret 相当の provider を検討する。

Server / Cloud では、OS user のローカル secret store よりも cloud KMS、HSM、PKCS#11、環境に応じた secret manager を使う方が適切な場合がある。

## 9. プロバイダ分類

`unlock_provider` は、unlock KEK を得るための具体実装・API・サービスを表す。`unlock_method` が抽象分類であるのに対して、`unlock_provider` はコード上の dispatch 単位である。

### 9.1 provider の大分類

| unlock_method | provider の性質 | 例 |
|---|---|---|
| `passphrase_kdf` | ユーザーが記憶するパスフレーズから KEK を導出する。 | `passphrase_argon2id`, `passphrase_pbkdf2_legacy` |
| `os_secret_store` | OS 保護ストアから exportable secret を取得する。 | `windows_dpapi_user`, `macos_keychain_generic_password`, `linux_secret_service` |
| `os_key_handle` | OS / TEE / Secure Enclave / Keystore 内の非抽出鍵に unwrap/decrypt を依頼する。 | `android_keystore_key`, `macos_secure_enclave_key`, `windows_cng_ncrypt_key` |
| `threshold_recovery` | 閾値秘密分散から recovery unlock KEK を復元する。 | `shamir_ssss`, `shamir_slip39` |
| `recovery_code_kdf` | 高エントロピー復旧コードや復旧フレーズから KEK を導出する。 | `recovery_code_argon2id`, `recovery_phrase_argon2id` |
| `hardware_token` | 外部ハードウェアトークン、スマートカード、HSM によって unlock する。 | `piv_smartcard`, `pkcs11_token`, `openpgp_card`, `fido2_prf` |
| `remote_kms` | リモート KMS / HSM に unwrap または key release を依頼する。 | `aws_kms`, `gcp_cloud_kms`, `azure_key_vault` |
| `remote_escrow` | 組織、管理者、別端末などの外部 escrow 経路で復旧または承認する。 | `org_admin_escrow`, `paired_device_escrow` |
| `test_only` | テスト専用。 | `test_static`, `test_ephemeral` |

### 9.2 provider に持たせる属性

`unlock_provider_tbl` には、provider インスタンスごとに変わる情報ではなく、provider 種別としての静的・準静的な性質を持たせる。

| カラム | 意味 | 例 |
|---|---|---|
| `unlock_provider` | provider の安定 ID。コード上の dispatch key。 | `windows_dpapi_user` |
| `unlock_method` | 抽象方式分類。 | `os_secret_store` |
| `config_schema_id` | `provider_config_json` の検証 schema ID。 | `windows_dpapi_user_v1` |
| `provider_display_name` | UI / ログ向け表示名。 | `Windows DPAPI Current User` |
| `description` | provider の説明。 | `Stores or protects an unlock secret under the current Windows user profile.` |
| `material_handling` | 鍵素材がどのように扱われるか。 | `exported_secret`, `non_exportable_key` |
| `locality` | ローカル完結か、リモート依存か。 | `local`, `remote`, `hybrid` |
| `user_presence_policy` | ユーザー操作・生体認証・タッチ等の要求可能性。 | `required`, `provider_dependent` |
| `production_status` | 本番利用可能性。 | `stable`, `experimental`, `test_only` |

### 9.3 material_handling

`material_handling` は、鍵素材がどこに現れるかを表す重要な分類である。

| material_handling | 意味 | 例 |
|---|---|---|
| `derived_in_memory` | パスフレーズや復旧コードから導出した鍵がアプリメモリに現れる。 | `passphrase_argon2id` |
| `exported_secret` | OS secret store から secret bytes を取得し、アプリメモリで使う。 | `windows_dpapi_user`, `macos_keychain_generic_password` |
| `non_exportable_key` | 鍵本体は取り出せず、key handle に暗号操作を依頼する。 | `android_keystore_key`, `macos_secure_enclave_key` |
| `remote_unwrap` | リモート KMS / HSM に unwrap を依頼する。 | `aws_kms`, `gcp_cloud_kms` |
| `threshold_reconstruction` | 複数 share から鍵または recovery material を復元する。 | `shamir_ssss` |

この属性は、メモリ保護方針、ログ禁止方針、ゼロ化方針、脅威モデルに影響する。

### 9.4 locality

`locality` は、unlock 処理がどこで完結するかを表す。

| locality | 意味 | 例 |
|---|---|---|
| `local` | 端末内で完結する。 | `passphrase_argon2id`, `windows_dpapi_user`, `android_keystore_key` |
| `remote` | 外部サービスへの通信が必要。 | `aws_kms`, `gcp_cloud_kms` |
| `hybrid` | ローカル処理と外部承認・外部デバイスが組み合わさる。 | `paired_device_escrow`, 一部の hardware token federation |

### 9.5 user_presence_policy

`user_presence_policy` は、ユーザー操作・生体認証・PIN・スマートカードタッチなどの要求可能性を表す。

| user_presence_policy | 意味 |
|---|---|
| `not_applicable` | ユーザー存在確認という概念が適用されない。 |
| `not_required` | 通常はユーザー操作を要求しない。 |
| `optional` | provider_config により要求できる。 |
| `required` | 方式上、ユーザー入力や share 入力などが必須。 |
| `provider_dependent` | OS 設定、鍵属性、デバイス能力に依存する。 |

生体認証は独立した unlock method ではない。生体認証は `os_secret_store` または `os_key_handle` のアクセス制御条件である。

### 9.6 provider_config_json との境界

`unlock_provider_tbl` は provider 種別の定義であり、`unlock_kek_tbl.provider_config_json` は個別インスタンスの設定である。

`provider_config_json` に入れてよい情報:

- Argon2id の salt、memory、iterations、parallelism
- Keychain の service/account
- DPAPI secret name
- Android Keystore alias
- Shamir threshold/share_count/share_set_id
- KMS key URI
- PIV slot

`provider_config_json` に入れてはいけない情報:

- `unlock_provider`
- `unlock_method`
- `platform`
- 平文 unlock KEK
- マスターパスワード
- Shamir share 本体
- 復旧コード本体

`unlock_provider`, `unlock_method`, `platform` はマスタテーブルや外部キーから分かるため、JSON に重複保存しない。

## 10. provider_config_json の例

### 8.1 passphrase_argon2id

```json
{
  "salt": "base64url...",
  "memory_kib": 262144,
  "iterations": 3,
  "parallelism": 4
}
```

パスワード本体は保存しない。

### 8.2 windows_dpapi_user

```json
{
  "scope": "current_user",
  "secret_name": "com.example.app.ulk-windows-dpapi-user-01"
}
```

DPAPI で保護された secret blob そのものを SQLite に置くか、OS 側の credential name を置くかは実装選択である。いずれの場合も平文 unlock KEK は保存しない。

### 8.3 macos_keychain_generic_password

```json
{
  "service": "com.example.app",
  "account": "ulk-macos-keychain-01"
}
```

### 8.4 android_keystore_key

```json
{
  "alias": "com.example.app.ulk-android-keystore-01",
  "user_authentication_required": true,
  "auth_timeout_seconds": 300,
  "hardware_backed_preferred": true
}
```

### 8.5 shamir_ssss

```json
{
  "threshold": 3,
  "share_count": 5,
  "share_set_id": "recovery-2026-05"
}
```

Shamir share 本体は SQLite に保存しない。SQLite には share set のメタデータだけを保存する。

### 8.6 aws_kms

```json
{
  "key_uri": "arn:aws:kms:ap-northeast-1:123456789012:key/00000000-0000-0000-0000-000000000000",
  "encryption_context_policy": "database-kek-v1"
}
```

## 9. 運用シナリオ

### 9.1 新規 DB 作成

1. `database_kek` を CSPRNG で生成する。
2. `key_tbl` に `database_kek` を登録する。
3. 少なくとも 1 つの `unlock_kek` 経路を作る。
4. `database_kek` を `unlock_kek` で wrap して `wrapped_key_tbl` に保存する。
5. 必要なら、マスターパスワード経路、OS 経路、Shamir recovery 経路を追加する。

### 9.2 秘匿 payload の保存

1. `record_dek` を CSPRNG で生成する。
2. `record_dek` を `key_tbl` に登録する。
3. `record_dek` を `database_kek` で wrap し、`wrapped_key_tbl` に保存する。
4. payload を canonical JSON bytes に変換する。
5. AAD context を生成する。
6. payload bytes を `record_dek` で AEAD 暗号化する。
7. `encrypted_object_tbl` に `object_uuid`, `schema_uuid`, `content_type`, `alg`, `kid`, `nonce`, `ciphertext`, `aad_policy` を保存する。

### 9.3 秘匿 payload の取得

1. `encrypted_object_tbl` から object を取得する。
2. `kid` から `record_dek` を特定する。
3. `record_dek` を wrap している `database_kek` を辿る。
4. `database_kek` を wrap している `unlock_kek` 経路を選ぶ。
5. `unlock_provider` に応じて unlock KEK または unwrap capability を取得する。
6. `database_kek` を unwrap する。
7. `record_dek` を unwrap する。
8. AAD context を再構成する。
9. payload を AEAD 復号する。
10. AAD 検証または認証タグ検証に失敗した場合、復号結果を破棄する。

### 9.4 マスターパスワード変更

payload や record DEK は再暗号化しない。新しいパスワードから新しい `unlock_kek` を導出し、同じ `database_kek` を新しい `unlock_kek` で wrap し直す。古い password unlock 経路は無効化または削除する。

### 9.5 OS unlock の追加

既存 `database_kek` を、新しい OS provider から得た `unlock_kek` で wrap する。payload や record DEK の再暗号化は不要である。

### 9.6 鍵ローテーション

`unlock_kek` のローテーションは、`database_kek` の wrap 行を再作成するだけでよい。

`database_kek` のローテーションは、すべての `record_dek` / `file_dek` の wrap 行を再作成する。

`record_dek` のローテーションは、該当 payload を復号し、新しい `record_dek` で再暗号化する。

## 10. 検索と blind index

暗号化 payload は通常ランダム nonce を使うため、同じ平文でも異なる ciphertext になる。したがって、平文検索や同一性判定を行いたい場合は、必要なフィールドだけに keyed blind index を導入する。

例:

```text
blind_index = HMAC-SHA256(index_key, normalized_value)
```

注意点:

1. 低エントロピー値への blind index は辞書攻撃や頻度分析に弱い。
2. 同じ値は同じ index になるため、等価性は漏れる。
3. `index_key` は payload 暗号化鍵とは分ける。
4. blind index 用フィールドは最小限にする。

## 11. セキュリティ仕様

### 11.1 目的と防御対象

本ライブラリの主要目的は、秘匿対象データを at-rest encryption により保護することである。主な防御対象は以下である。

1. SQLite データベースファイル単体の漏洩。
2. バックアップファイルの漏洩。
3. 同期先ストレージやクラウド保存先からの暗号化済み DB の漏洩。
4. アプリケーションがロック状態であり、unlock material が利用できない状態での DB 読み取り。
5. 破棄済みまたは無効化済み unlock 経路の不正利用。

この範囲では、payload を `record_dek` / `file_dek` で AEAD 暗号化し、DEK を `database_kek` で wrap し、`database_kek` を複数の `unlock_kek` 経路で wrap する構造により、DB ファイルだけを取得した攻撃者が平文を得ることを防ぐ。

### 11.2 限界と非目標

同一 OS ユーザー権限で実行されるマルウェア、特に infostealer に対して、完全な機密性は保証しない。これは暗号ストレージ設計だけでは解決できない。

同一ユーザー権限の攻撃者は、正規アプリケーションが利用できる OS API、OS secret store、プロセス間通信、クリップボード、スクリーンキャプチャ、アクセシビリティ API、キーロガー、ブラウザデータ、アプリのメモリ空間などを狙える可能性がある。

したがって、本仕様は以下を非目標とする。

1. アプリが unlock 済みで、平文 payload を表示または利用している瞬間の完全防御。
2. 同一 OS ユーザー権限のマルウェアによるキーロギングの完全防御。
3. スクリーンキャプチャ、クリップボード監視、アクセシビリティ API 悪用の完全防御。
4. 管理者権限またはカーネル権限を持つ攻撃者に対する完全防御。
5. 侵害済み端末上での完全な秘密保持。

ただし、同一ユーザー権限マルウェアに対しても、被害を低減するための設計は行う。

### 11.3 同一ユーザー権限マルウェアへの低減策

同一 OS ユーザー権限の infostealer への対策は、完全防御ではなく、露出時間、露出範囲、一括窃取可能性を下げる方針とする。

推奨 policy は以下である。

1. OS secret store による自動 unlock は便利機能として扱い、高セキュリティモードでは無効化可能にする。
2. `passphrase_kdf`, `hardware_token`, `os_key_handle`, user presence を要求する provider を選択可能にする。
3. 復号済み payload、`database_kek`, `record_dek`, `file_dek` のメモリ滞在時間を短くする。
4. 平文 payload の永続キャッシュを禁止する。
5. 復号済み検索キャッシュを保存しない。
6. クリップボードへのコピーは短時間 TTL で自動消去する。
7. bulk export や background decrypt は policy で制限できるようにする。
8. secure mode では per-item decrypt または per-session unlock を選択可能にする。
9. provider policy により、`os_secret_store` だけで unlock できる構成を禁止できるようにする。
10. 可能な platform では `os_key_handle` や hardware-backed provider を優先可能にする。

### 11.4 security mode の例

実装は、少なくとも通常モードと高セキュリティモードを区別できるようにすることが望ましい。

```text
normal mode:
  OS secret store unlock allowed
  decrypted session cache allowed with TTL
  clipboard allowed with auto-clear

secure mode:
  passphrase or user presence required after app start
  OS auto-unlock disabled or combined with second factor
  decrypt-on-demand preferred
  decrypted cache disabled or very short TTL
  clipboard auto-clear mandatory
  bulk export restricted

paranoid mode, optional:
  hardware token or os_key_handle required
  no persistent session key cache
  no background unlock
  per-item decrypt confirmation
  recovery path separated from daily-use path
```

### 11.5 OS secret store と OS key handle のリスク差

`os_secret_store` は、OS が保護する secret をアプリケーションが取得し、その secret bytes をメモリ上で使う方式である。同一ユーザー権限マルウェアが同じ API を悪用できる場合、unlock secret が奪われる可能性がある。

`os_key_handle` は、鍵素材をアプリケーションに取り出さず、OS、TEE、Secure Enclave、Android Keystore、TPM などの内部鍵に unwrap/decrypt を依頼する方式である。上位鍵素材の一括抽出を難しくできるが、正規アプリの操作を悪用される場合や、unwrap 後の下位鍵がアプリメモリに出る設計ではリスクが残る。

したがって、`os_key_handle` は `os_secret_store` より強い境界を作り得るが、同一ユーザー権限マルウェアに対する完全解ではない。

### 11.6 メタデータ漏洩

本仕様では、以下のメタデータは平文で保存され得る。

- `object_uuid`
- `schema_uuid`
- `content_type`
- `kid`
- `key_class`
- `purpose`
- `alg`
- `status`
- `created_at_ms`
- `updated_at_ms`
- `unlock_provider`
- `platform`
- `support_level`
- `implementation_status`

これらは payload 本文ではないが、利用状況、データ種別、更新時刻、鍵構成、使用 platform を示すメタデータである。メタデータ漏洩をどこまで許容するかは threat model で明示する必要がある。

より強い秘匿性が必要な場合は、`content_type`, `schema_uuid`, provider 情報、作成時刻などの粒度を粗くする、または一部を暗号化 payload 内へ移すことを検討する。ただし、検索、同期、migration、復旧性とのトレードオフがある。

### 11.7 ログとキャッシュ

以下をログに出力してはならない。

1. 平文 payload。
2. マスターパスワード。
3. 復旧コード。
4. Shamir share 本体。
5. 平文 `unlock_kek`, `database_kek`, `record_dek`, `file_dek`, `index_key`。
6. 復号済み JSON。
7. provider から取得した secret bytes。

`kid`, `object_uuid`, `schema_uuid`, provider 名、platform 名はログ出力可能な場合があるが、これらもメタデータ漏洩になり得るため、debug log と production log で扱いを分ける。

平文 payload の永続キャッシュは禁止する。メモリキャッシュを許可する場合は TTL と明示的な purge API を持たせる。

### 11.8 鍵破棄

破棄済み鍵は物理削除ではなく、`key_tbl.status = 'destroyed'` による論理削除とする。台帳行は監査、履歴、参照整合性のため保持する。

`status = 'destroyed'` の鍵は、新規暗号化、unwrap、復号に使用してはならない。wrap 済み鍵材料を物理削除するかどうかは別途 policy で定める。物理削除する場合も、台帳上は destroyed として残す。

### 11.9 暗号文の可搬性

暗号文は可搬でなければならない。ここでの可搬性とは、同じ仕様を実装する別プロセス、別端末、別 OS、別プログラミング言語の実装が、必要な鍵材料と provider 条件を満たす限り、同じ暗号文を復号できることを意味する。

可搬性のため、以下を必須とする。

1. 暗号 envelope は versioned format とする。
2. `v`, `type`, `alg`, `kid`, `nonce`, `ct`, `aad_policy` の意味を固定する。
3. JSON は常に canonical JSON として正規化する。
4. JSON 文字列は UTF-8 とする。
5. 外部表現ではバイナリ値を base64url without padding で表す。
6. SQLite 内部で BLOB 保存する場合も、外部エクスポート時の JSON envelope 形式を定義する。
7. `kid` は UUIDv4 の小文字ハイフン付き canonical string とする。
8. `alg` の意味は実装依存にしない。`A256GCM` なら AES-256-GCM として固定する。
9. AES-GCM の `ct` は ciphertext と authentication tag を結合した bytes とするか、分離するかを仕様で固定する。本仕様では結合形式を標準とする。
10. nonce 長、tag 長、AAD 生成規則を仕様化する。

標準 JSON envelope は以下である。

```json
{
  "v": 1,
  "type": "aead",
  "alg": "A256GCM",
  "kid": "550e8400-e29b-41d4-a716-446655440000",
  "nonce": "base64url-no-padding",
  "ct": "base64url-no-padding",
  "aad_policy": "record-payload-v1"
}
```

SQLite 内部表現では、`nonce` と `ciphertext` を BLOB として保持してよい。ただし、外部交換・バックアップ・テストベクターでは canonical JSON envelope へ変換できなければならない。

### 11.10 テストベクター

実装者が正しさと相互運用性を確認できるよう、公式 test vector を用意する。

テストベクターは以下を含む。

1. payload 暗号化ベクター。
2. database KEK wrap ベクター。
3. record DEK wrap ベクター。
4. AAD 不一致による復号失敗ベクター。
5. JSON 正規化ベクター。
6. UUIDv4 `kid` 検証ベクター。
7. provider_config_json 正規化ベクター。
8. blind index を採用する場合は HMAC ベクター。

payload 暗号化 test vector は、最低限以下のフィールドを含む。

```json
{
  "name": "record-payload-a256gcm-v1-basic",
  "plaintext_json": {
    "title": "example login",
    "username": "alice@example.com",
    "password": "correct horse battery staple"
  },
  "canonical_plaintext_hex": "...",
  "key": {
    "kid": "550e8400-e29b-41d4-a716-446655440000",
    "k": "base64url-no-padding-32-bytes"
  },
  "nonce": "base64url-no-padding-12-bytes",
  "aad_policy": "record-payload-v1",
  "aad_context_json": {
    "v": 1,
    "aad_policy": "record-payload-v1",
    "object_uuid": "...",
    "schema_uuid": "...",
    "content_type": "application/json; profile=\"https://example.invalid/schema/login-v1\"",
    "kid": "550e8400-e29b-41d4-a716-446655440000",
    "alg": "A256GCM"
  },
  "canonical_aad_hex": "...",
  "ciphertext_and_tag": "base64url-no-padding",
  "envelope": {
    "v": 1,
    "type": "aead",
    "alg": "A256GCM",
    "kid": "550e8400-e29b-41d4-a716-446655440000",
    "nonce": "base64url-no-padding-12-bytes",
    "ct": "base64url-no-padding",
    "aad_policy": "record-payload-v1"
  }
}
```

テストベクターでは、通常運用では禁止される固定 nonce を使ってよい。これは再現性のためであり、本番実装では固定 nonce を使ってはならない。

復号失敗ベクターでは、以下のような改変を加えた場合に認証失敗することを確認する。

1. `object_uuid` を変更する。
2. `schema_uuid` を変更する。
3. `content_type` を変更する。
4. `kid` を変更する。
5. `nonce` を変更する。
6. `ct` の 1 bit を変更する。
7. `aad_policy` を変更する。

### 11.11 実装者向けセキュリティチェックリスト

1. CSPRNG で鍵を生成しているか。
2. AES-GCM nonce が同一鍵で再利用されないか。
3. AAD が canonical JSON から生成されているか。
4. JSON 保存前に必ず正規化しているか。
5. `alg` と `key_tbl.alg` と `key_profile_tbl.alg` の整合性を検証しているか。
6. `status = destroyed`, `disabled` の鍵を使用拒否しているか。
7. `test_only` provider を production policy で拒否しているか。
8. 平文鍵と平文 payload をログ出力していないか。
9. provider_config_json に provider/method/platform を重複保存していないか。
10. provider_config_json を provider ごとの schema で検証しているか。
11. unlock provider が platform policy に適合しているか。
12. OS secret store だけに依存しない復旧経路があるか。
13. バックアップ復元テストを実施しているか。
14. test vector による相互運用確認を実施しているか。

## 12. 決定済み事項と残検討事項

### 12.1 決定済み事項

以下は仕様として確定する。

1. `kid` は UUIDv4 文字列とする。
2. JSON は常に正規化する。少なくとも SQLite に保存する JSON、AAD 生成に使う JSON、暗号化前 payload JSON、署名・MAC・ハッシュ・UUID 生成対象 JSON は正規化対象である。
3. 破棄済み鍵は物理削除ではなく論理削除とする。`key_tbl.status = 'destroyed'` を使い、台帳行は保持する。
4. `root_kek` ではなく `unlock_kek` を使う。
5. `unlock_method` は抽象分類、`unlock_provider` は具体実装、`unlock_kek_tbl` は個別 unlock 経路を表す。
6. `unlock_kek_tbl` には `unlock_method` を置かず、`unlock_provider` から導出する。
7. `method_config_json` ではなく `provider_config_json` と呼ぶ。
8. `provider_config_json` には `unlock_provider`, `unlock_method`, `platform` を重複保存しない。
9. provider と platform の関係は多対多とする。
10. 生体認証は独立した unlock method ではなく、`os_secret_store` または `os_key_handle` のアクセス制御条件として扱う。
11. Shamir secret sharing は通常復号経路ではなく、復旧用 unlock 経路として扱う。
12. 平文鍵、マスターパスワード、Shamir share、復旧コード本体は SQLite に保存しない。
