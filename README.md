# Encrypted Database Library

[![Python Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-python.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-python.yml)
[![Integration Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-integration.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-integration.yml)
[![Node.js Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-nodejs.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-nodejs.yml)
[![Browser Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-browser.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-browser.yml)
[![Go Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-go.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-go.yml)
[![Rust Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-rust.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-rust.yml)
[![Read-Only Matrix Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-readonly-matrix.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-readonly-matrix.yml)
[![Write Matrix Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-write-matrix.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-write-matrix.yml)
[![Coverage](https://codecov.io/gh/TakashiSasaki/vault.moukaeritai.work/branch/vault.moukaeritai.work/graph/badge.svg)](https://codecov.io/gh/TakashiSasaki/vault.moukaeritai.work/tree/vault.moukaeritai.work)

**Status:** Storage Format V1 は Stable です。ただし、ライブラリの packaging、追加 unlock provider、key rotation、blind index、追加言語実装などは引き続き開発中です。

**公開サイト / ドキュメント:** [https://vault.moukaeritai.work/](https://vault.moukaeritai.work/)

これは新しく作成する暗号化データベース（暗号化ストレージ）のライブラリです。
SQLite などのローカル永続化層に秘匿対象データを保存するアプリケーション向けに、アプリケーション層暗号化、鍵階層、鍵ラッピング、アンロック手段、復旧経路、検索用補助鍵を統一的に扱う機能を提供します。

詳細な仕様・設計文書については、[ドキュメント入口 (docs/README.md)](docs/README.md) を参照してください。

## リポジトリ構造と対応言語

当リポジトリはモノレポ構成となっており、以下の言語向けのライブラリを提供します（他の言語についても将来的に追加する可能性があります）。

```text
.
├── docs/               # 仕様書・設計ドキュメント
├── python/             # Python 向け baseline implementation
├── nodejs/             # Node.js 向け baseline implementation
├── browser-test/       # browser/sql.js 向けテスト実装・検証ハーネス
├── go/                 # Go ポータビリティ検証・writer scaffold
├── rust/               # Rust ポータビリティ検証・writer scaffold
├── zig/                # Zig selected read-only fixture decrypt validation scaffold
├── integration-tests/  # クロス言語 roundtrip / read-only matrix / write-matrix 検証
└── scripts/            # ローカル実行スクリプトとドキュメント guardrail
```

### docs/
仕様書や設計ドキュメントを配置しています。

### Python
Python 向けの baseline implementation です。
詳細は [Python用 README](python/README.md) を参照してください。

### Node.js
Node.js 向けの baseline implementation です。
詳細は [Node.js用 README](nodejs/README.md) を参照してください。

### browser-test/
browser/sql.js 向けのテスト実装・検証ハーネスです。Jest JSDOM/sql.js 環境での検証を含みますが、完全な real-browser WebCrypto runtime coverage を意味するものではありません。

### Go
Go 実装は Storage Format V1 のポータビリティ検証と writer scaffold を目的としたものです。現時点では full production storage library ではありません。

### Rust
Rust 実装も同様に、Storage Format V1 のポータビリティ検証と writer scaffold を目的としたものです。現時点では full production storage library ではありません。

### Zig
Zig currently provides a smoke test and an initial read-only Storage Format V1 validation and decrypt scaffold. It can consume selected existing V1 SQLite fixtures using the passphrase provider. Zig remains scaffold-level and is not a production storage library, nor does it provide a public storage API or writer support.

### integration-tests/
クロス言語の roundtrip、read-only matrix、write-matrix 検証ハーネスを含みます。

### scripts/
ローカル環境でのテスト実行やカバレッジ測定、ドキュメントの鮮度確認などを行うスクリプト群です。

## 主な特徴

- データの暗号化: payload を AEAD (例: AES-256-GCM) で暗号化し、非秘密メタデータのみを平文で保存
- 柔軟な鍵階層: `unlock_kek` -> `database_kek` -> `record_dek` / `file_dek` といった階層構造による柔軟な鍵管理
- 複数アンロック経路: パスワード（Argon2id）、OS のシークレットストア（DPAPI、Keychain 等）、Shamir の秘密分散法などをサポート（予定）
- 検索可能性: HMAC などを利用した Blind Index による、暗号化データのセキュアな検索

## インストールと使い方
各言語ディレクトリの README ファイルをご参照ください。

## Testing and Coverage

### Local Test Commands

You can run a baseline aggregate test command for the core languages using the top-level orchestration script:

```bash
# Run baseline tests (Python, Node.js, Browser, and Roundtrip Integration)
./scripts/test_all.sh
```

Alternatively, you can run individual tests or matrices manually for troubleshooting:
- **Python tests**: `cd python && pytest`
- **Node.js tests**: `cd nodejs && npm test`
- **browser-test tests**: `cd browser-test && npm test`
- **Go tests**: `cd go && go test ./...`
- **Rust tests**: `cd rust && cargo test`
- **Zig tests**: `cd zig && zig build run` and `cd zig && zig build test`
- **roundtrip integration tests**: `./integration-tests/roundtrip/test_roundtrip.sh`
- **read-only matrix tests**: `./integration-tests/read-only-matrix/test_readonly_matrix.sh`
- **write-matrix tests**: `bash integration-tests/write-matrix/test_writer_matrix.sh`

### Local Coverage Commands

Coverage across all languages can be measured and reported by running:

```bash
# Measure and collect coverage artifacts
./scripts/coverage_all.sh
```

You can also run coverage individually:
- **Python**: `cd python && pytest --cov=src --cov-report=xml --cov-report=term`
- **Node.js**: `cd nodejs && npm run test:coverage`
- **Browser**: `cd browser-test && npm run test:coverage`

*Note regarding Browser-test Coverage*: The browser-test coverage measures execution in the Jest JSDOM/sql.js harness environment. It does not represent full browser real-runtime (WebCrypto) coverage.

### CI Workflows

Our CI workflows run on standard `ubuntu-latest` environments and are split into independent jobs for stability and clarity:
- Python Tests
- Node.js Tests
- Browser Tests
- Go Tests
- Rust Tests
- Zig Smoke Test
- Integration Tests / Roundtrip
- Read-only Matrix
- Write Matrix

Coverage results are generated during the test runs and uploaded to GitHub Actions artifacts as `python-coverage`, `nodejs-coverage`, and `browser-test-coverage`.

*Note: Local coverage commands only generate reports. The actual upload to Codecov is performed during GitHub Actions CI runs using tokenless OIDC authentication (`use_oidc: true`). Python, Node.js, and Browser-test coverage are segmented using Codecov flags (`python`, `nodejs`, `browser-test`). The top-level README shows an overall Codecov coverage badge. As previously noted, the browser-test coverage is generated via the Jest JSDOM/sql.js harness and does not represent real browser runtime coverage.*
