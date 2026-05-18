# Encrypted Database Library

[![Python Tests](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-python.yml/badge.svg)](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-python.yml)
[![Python Coverage](https://codecov.io/gh/TakashiSasaki/encrypted-database/graph/badge.svg?flag=python)](https://codecov.io/gh/TakashiSasaki/encrypted-database)
[![Node.js Tests](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-nodejs.yml/badge.svg)](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-nodejs.yml)
[![Node.js Coverage](https://codecov.io/gh/TakashiSasaki/encrypted-database/graph/badge.svg?flag=nodejs)](https://codecov.io/gh/TakashiSasaki/encrypted-database)
[![Browser Tests](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-browser.yml/badge.svg)](https://github.com/TakashiSasaki/encrypted-database/actions/workflows/test-browser.yml)
[![Browser Coverage](https://codecov.io/gh/TakashiSasaki/encrypted-database/graph/badge.svg?flag=browser)](https://codecov.io/gh/TakashiSasaki/encrypted-database)

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
