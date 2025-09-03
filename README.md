# GCP災害対応AIエージェントシステム

GCPを基盤としたマルチエージェント災害対応システムです。ニュース/SNS/公的機関の情報から災害を自動検知し、リアルタイムで情報収集・分析・対策立案・広報・支援レポートを実行します。

## アーキテクチャ

### マルチエージェント構成
- **災害検知Agent**: RSS/API監視 → Vertex AI判定 → Pub/Sub発行
- **オーケストレータAgent**: LangGraph状態管理 → 各Agentタスク配信
- **情報収集Agent**: 公的情報/ニュース取込 → RAG構築
- **対策検討Agent**: RAG参照 → BigQuery GIS分析 → 被害推定・対応策
- **広報Agent**: Firestore → リアルタイムWeb配信
- **サポートAgent**: 心理/経済分析 → 行政レポート　※優先度低※

### 技術スタック
- **言語**: Python 3.11, TypeScript
- **AI**: Vertex AI (Gemini 1.5 Pro/Flash)
- **インフラ**: Cloud Run, Pub/Sub, Firestore, BigQuery
- **オーケストレーション**: LangGraph, Cloud Tasks
- **IaC**: Terraform

## ディレクトリ構成

```
disaster-response-system/
├── agents/                 # マルチエージェント実装
│   ├── common/            # 共通ライブラリ
│   ├── detection/         # 災害検知Agent
│   ├── orchestrator/      # オーケストレータAgent
│   ├── info_collector/    # 情報収集Agent
│   ├── analyzer/         # 対策検討Agent
│   └── pr/               # 広報Agent
├── infrastructure/        # Terraformインフラ定義
│   ├── modules/          # 再利用可能モジュール
│   └── environments/     # 環境別設定
├── shared/               # 共有コード・設定
│   ├── models/           # データモデル
│   ├── utils/            # ユーティリティ
│   └── config/           # 設定ファイル
├── web/                  # フロントエンド（別途実装予定）
└── scripts/              # デプロイスクリプト
```

## デプロイ方法

### 前提条件
- GCPプロジェクト作成済み
- gcloud CLI認証済み
- Docker & Terraform インストール済み

### 環境変数設定
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="asia-northeast1"
```

### デプロイ実行
```bash
./scripts/deploy.sh
```

## ローカル開発

### 開発環境起動
```bash
docker-compose up
```

### エージェント個別テスト
```bash
# 災害検知テスト
curl -X POST http://localhost:8081/detect

# オーケストレーション確認
curl http://localhost:8082/health

# 情報収集状況確認
curl http://localhost:8083/health
```

## 運用監視

- **ログ**: Cloud Logging
- **メトリクス**: Cloud Monitoring
- **トレース**: Cloud Trace
- **エラー**: Error Reporting

## セキュリティ

- IAM最小権限
- Service Account分離
- Secret Manager
- VPC Service Controls対応