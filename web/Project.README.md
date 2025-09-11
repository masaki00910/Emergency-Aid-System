# Disaster Response System - Frontend

このディレクトリは災害対応システムのフロントエンド実装用です。

## 構成予定

```
web/
├── public/          # 静的ファイル
├── src/             # Next.js/React実装
│   ├── components/  # UIコンポーネント
│   ├── pages/       # ページコンポーネント
│   ├── hooks/       # カスタムフック
│   ├── utils/       # ユーティリティ
│   └── types/       # TypeScript型定義
└── functions/       # Cloud Functions
```

## 技術スタック

- Next.js 14 + TypeScript
- Firestore SDK (リアルタイム更新)
- Google Maps JavaScript API
- Tailwind CSS

## 主要機能

1. **災害情報ダッシュボード**
   - リアルタイム災害情報表示
   - 地図ベースの可視化
   - 影響地域・避難所情報

2. **モバイル対応**
   - レスポンシブデザイン
   - PWA対応
   - プッシュ通知

3. **アクセシビリティ**
   - 緊急時軽量版
   - 多言語対応
   - 色弱対応

## データソース

- Firestore: `incidents`, `bulletins`, `analysis_results`
- リアルタイム更新: Firestore リスナー
- 地図データ: Google Maps API

別チームでの実装をお待ちしています。