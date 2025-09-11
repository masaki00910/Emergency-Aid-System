# Disaster Response System - Frontend

災害対応システムのフロントエンド実装リポジトリです。  
Next.js 14 + TypeScript + TailwindCSS + Firebase Firestore + Google Maps JavaScript API を利用しています。

---

## 📂 プロジェクト構成
```
web/
├── public/          # 静的ファイル（アイコン、画像など）
├── src/
│   ├── components/  # UIコンポーネント
│   ├── pages/       # ページコンポーネント
│   ├── hooks/       # カスタムフック
│   ├── utils/       # ユーティリティ
│   └── types/       # TypeScript型定義
└── functions/       # Cloud Functions（必要に応じて）
```

---

## 🚀 開発環境のセットアップ

### 1. リポジトリをクローン
```bash
git clone <このリポジトリURL>
cd web
```

### 2. 依存関係のインストール
```bash
npm install
```

### 3. 環境変数ファイルの作成
ルート直下に `.env.local` を作成してください。

```bash
touch .env.local
```

内容:
```env
# Google Cloud Console で取得した Maps JavaScript APIのKey を入力してください
(ジョンが発行しておきましたが、ハードコーディング避けています)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=ここに自分のAPIキーを入れる
```

### 4. 開発サーバー起動
```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開くとアプリが表示されます。

---

## 🗺️ 主な機能

- **災害情報ダッシュボード**
  - Google Maps 上にインシデント（地震・大雨・土砂災害など）をピン表示  
    - 赤ピン = Active  
    - 青ピン = Inactive
  - ピンをクリックすると詳細カードを表示し、関連フィードをハイライト

- **フィード表示**
  - NHK / JMA / Tenki / SNS(X) 等のフィードを一覧表示  
  - インシデントに紐づくフィードは強調表示（淡い黄色 + 最上位ソート）

- **アラート**
  - Firestore / API から取得した警報・注意報をカード形式で表示

---

## 🔑 環境変数について

| 変数名 | 用途 | 設定方法 |
|--------|------|----------|
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Google Maps JavaScript API を利用するためのキー | [Google Cloud Console](https://console.cloud.google.com/) で API キーを発行し入力 |

---

## 📚 参考リンク
- [Next.js Documentation](https://nextjs.org/docs)
- [Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/overview)
- [Firebase Firestore](https://firebase.google.com/docs/firestore)

---

## 📦 デプロイ
本番環境デプロイは Vercel を想定しています。

```bash
vercel --prod
```

詳細: [Next.js デプロイガイド](https://nextjs.org/docs/app/building-your-application/deploying)

---

## 📝 補足
- バックエンドとの API/Firestore スキーマ仕様は `docs/backend_api_spec.md` を参照してください。
- Mock データは `src/mocks/` にあります。開発初期はこれを利用して UI を確認できます。

---
