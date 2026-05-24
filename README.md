# Encrypted Database Library

[![Python Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-python.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-python.yml)
[![Integration Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-integration.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-integration.yml)
[![Node.js Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-nodejs.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-nodejs.yml)
[![Browser Tests](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-browser.yml/badge.svg)](https://github.com/TakashiSasaki/vault.moukaeritai.work/actions/workflows/test-browser.yml)

これは新しく作成する暗号化データベース（暗号化ストレージ）のライブラリです。
SQLite などのローカル永続化層に秘匿対象データを保存するアプリケーション向けに、アプリケーション層暗号化、鍵階層、鍵ラッピング、アンロック手段、復旧経路、検索用補助鍵を統一的に扱う機能を提供します。

詳細な仕様・設計文書については、[ドキュメント入口 (docs/README.md)](docs/README.md) を参照してください。

## リポジトリ構造と対応言語

当リポジトリはモノレポ構成となっており、以下の言語向けのライブラリを提供します（他の言語についても将来的に追加する可能性があります）。

```text
.
├── docs/       # 仕様書・設計ドキュメント
├── python/     # Python 向けライブラリ実装
└── nodejs/     # Node.js 向けライブラリ実装
```

### Python
Python 用の実装は `python/` ディレクトリに配置されています。
詳細は [Python用 README](python/README.md) を参照してください。

### Node.js
Node.js 用の実装は `nodejs/` ディレクトリに配置されています。
詳細は [Node.js用 README](nodejs/README.md) を参照してください。

## 主な特徴

- データの暗号化: payload を AEAD (例: AES-256-GCM) で暗号化し、非秘密メタデータのみを平文で保存
- 柔軟な鍵階層: `unlock_kek` -> `database_kek` -> `record_dek` / `file_dek` といった階層構造による柔軟な鍵管理
- 複数アンロック経路: パスワード（Argon2id）、OS のシークレットストア（DPAPI、Keychain 等）、Shamir の秘密分散法などをサポート（予定）
- 検索可能性: HMAC などを利用した Blind Index による、暗号化データのセキュアな検索

## インストールと使い方
各言語ディレクトリの README ファイルをご参照ください。

## Testing and Coverage

### Local Test Commands

You can run the full suite of tests using the top-level orchestration script:

```bash
# Run all tests (Python, Node.js, Browser, and Roundtrip Integration)
./scripts/test_all.sh
```

Alternatively, you can run individual tests manually for troubleshooting:
- **Python**: `cd python && pytest`
- **Node.js**: `cd nodejs && npm test`
- **Browser**: `cd browser-test && npm test`
- **Roundtrip**: `./integration-tests/roundtrip/test_roundtrip.sh`

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
- Integration Roundtrip Tests

Coverage results are generated during the test runs and uploaded to GitHub Actions artifacts as `python-coverage`, `nodejs-coverage`, and `browser-test-coverage`.

*Note: Local coverage commands only generate reports. The actual upload to Codecov is performed during GitHub Actions CI runs. Python, Node.js, and Browser-test coverage are distinguished using Codecov flags (`python`, `nodejs`, `browser-test`). The coverage badge will be added to the top of this README once the Codecov project setup is complete and the badge URL is verified. Also note that the browser-test coverage measures execution in the Jest JSDOM/sql.js harness environment, and does not represent full browser real-runtime coverage.*
