# 🛰️ 札幌駅新幹線工事 変化ビューア

北海道新幹線延伸工事エリアをSentinel-2衛星画像で時系列比較するWebアプリ。

![スクリーンショット](docs/screenshot.png)

## 概要

- **衛星データ**: Copernicus Sentinel-2 (無料・欧州宇宙機関)
- **対象エリア**: 札幌駅周辺・創成川エリア (北海道新幹線延伸工事箇所)
- **期間**: 2020年〜現在 (月1枚取得)
- **雲量フィルター**: 20%以下優先

---

## システム構成

```
sapporo-satellite/
├── backend/               # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py        # FastAPIアプリ本体
│   │   └── api/
│   │       └── images.py  # 画像APIエンドポイント
│   ├── data/
│   │   ├── images/        # 衛星画像PNG (git管理外)
│   │   └── metadata/      # メタデータJSON
│   ├── fetch_images.py    # Sentinel-2取得スクリプト (本番用)
│   ├── generate_mock_data.py  # 開発用モックデータ生成
│   └── requirements.txt
├── frontend/              # Next.js フロントエンド
│   └── src/
│       ├── app/           # Next.js App Router
│       ├── components/    # Reactコンポーネント
│       │   ├── SatelliteMap.tsx    # Leaflet地図
│       │   ├── TimelineSlider.tsx  # 時系列スライダー
│       │   └── ControlPanel.tsx    # 操作パネル
│       ├── hooks/
│       │   └── useImages.ts  # データ取得フック
│       └── lib/
│           └── api.ts        # APIクライアント
├── render.yaml            # Renderデプロイ設定
└── README.md
```

---

## ⚡ クイックスタート (ローカル)

### 前提条件

- Python 3.11以上
- Node.js 20以上
- Git

---

### 1. リポジトリをクローン

```bash
git clone https://github.com/あなたのユーザー名/sapporo-satellite.git
cd sapporo-satellite
```

---

### 2. バックエンドをセットアップ

```bash
cd backend

# 仮想環境を作成して有効化
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 依存ライブラリをインストール
pip install -r requirements.txt

# .envを作成 (後でCopernicusアカウントを入力)
cp .env.example .env

# 【まず試す】モックデータを生成 (アカウント不要)
python generate_mock_data.py

# FastAPIサーバーを起動
uvicorn app.main:app --reload --port 8000
```

ブラウザで http://localhost:8000/docs を開くとAPIドキュメントが見えます。

---

### 3. フロントエンドをセットアップ

別のターミナルを開いて:

```bash
cd frontend

# .env.localを作成
cp .env.local.example .env.local

# 依存ライブラリをインストール
npm install

# 開発サーバーを起動
npm run dev
```

ブラウザで http://localhost:3000 を開いてください。

---

### 4. 本物の衛星画像を取得する (任意)

モックデータで動作確認できたら、本物の衛星画像を取得します。

#### 4-1. Copernicusアカウント作成 (無料)

1. https://dataspace.copernicus.eu/ にアクセス
2. 「Register」からアカウント作成
3. メール確認を完了する

#### 4-2. .envに認証情報を設定

```bash
# backend/.env
CDSE_USER=登録したメールアドレス
CDSE_PASSWORD=パスワード
```

#### 4-3. 衛星画像を取得

```bash
cd backend
source venv/bin/activate

# 全期間 (2020年〜現在) を取得
python fetch_images.py

# 特定の月だけ取得
python fetch_images.py --month 2024-06

# 雲量10%以下で絞る
python fetch_images.py --max-cloud 10
```

---

## 🌐 API リファレンス

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/images` | 画像一覧 (フィルタ可) |
| GET | `/api/images/latest` | 最新画像 |
| GET | `/api/images/{date}` | 指定日の画像 |
| GET | `/api/images/{date}/file` | 画像ファイル直接取得 |

### クエリパラメータ

`GET /api/images?year=2024&max_cloud=15`

| パラメータ | 型 | 説明 |
|-----------|---|------|
| year | int | 年でフィルタ |
| month | int | 月でフィルタ |
| max_cloud | float | 雲量上限(%) |

---

## 🚀 Renderへのデプロイ

### 1. GitHubリポジトリを作成

```bash
# GitHubでリポジトリ作成後
cd sapporo-satellite
git init
git add .
git commit -m "Initial commit: 札幌駅新幹線工事変化ビューア"
git branch -M main
git remote add origin https://github.com/ユーザー名/sapporo-satellite.git
git push -u origin main
```

### 2. RenderでBlueprint設定

1. https://render.com にログイン (GitHubアカウントで)
2. 「New +」→「Blueprint」
3. GitHubリポジトリを選択
4. `render.yaml` が自動検出される
5. 「Apply」をクリック

### 3. 環境変数を設定

Renderダッシュボードの `sapporo-satellite-api` サービスで:

| キー | 値 |
|-----|---|
| CDSE_USER | Copernicusのメールアドレス |
| CDSE_PASSWORD | Copernicusのパスワード |

### 4. デプロイ後の確認

- フロントエンド: `https://sapporo-satellite.onrender.com`
- バックエンドAPI: `https://sapporo-satellite-api.onrender.com/docs`

> ⚠️ Renderの無料プランはアクセスがないとスリープします。初回アクセスは30秒ほどかかります。

---

## 🛠️ よくあるエラーと対処法

### バックエンドが起動しない

```
ModuleNotFoundError: No module named 'fastapi'
```
→ 仮想環境が有効になっていません。`source venv/bin/activate` を実行してください。

---

### 地図が表示されない (フロントエンド)

```
Error: Leaflet is not defined
```
→ Leafletは自動的にSSR無効化されています。ブラウザのキャッシュをクリアして再試行してください。

---

### APIに接続できない

フロントエンドのブラウザコンソールに CORS エラーが出る場合:

1. `backend/app/main.py` の `allow_origins` に `http://localhost:3000` が入っているか確認
2. バックエンドが `8000` ポートで起動しているか確認

---

### Copernicus 認証エラー

```
❌ 認証失敗: 401 Unauthorized
```
→ `.env` のメールアドレスとパスワードを確認。アカウント登録後、メール確認が完了しているか確認。

---

### 衛星画像が見つからない (雲量エラー)

```
⚠️ 2024-02: 雲量20%以下の画像なし
```
→ 冬季は雲が多く画像が取得できないことがあります。`--max-cloud 40` で上限を上げて試してください。

---

## 🔭 次にやるべき改善案 TOP10

### 技術的改善

1. **🤖 AIによる工事変化検知**
   - Python + OpenCV で差分検出
   - PyTorch で変化領域をハイライト
   - 工事進捗率を自動計算

2. **⏱️ タイムラプス動画生成**
   - FFmpegで画像列をMP4に変換
   - ブラウザ内プレビュー
   - ダウンロードボタン

3. **🔍 衛星画像の並列比較 (スプリットビュー)**
   - 左右分割で2枚同時表示
   - ドラッグで比較境界を移動

4. **🏢 建物増減検知 (NDBI)**
   - 正規化建物指数を計算
   - 建設・解体エリアを色分け

5. **🌍 対象エリア拡張**
   - 北海道全域の工事箇所に対応
   - 座標検索ボックスを追加

### UX改善

6. **📊 工事進捗ダッシュボード**
   - 変化ピクセル数のグラフ表示
   - 月次レポートPDF出力

7. **🔔 プッシュ通知**
   - 新画像取得時にメール/LINE通知
   - GitHub Actions でスケジュール取得

8. **💾 データベース導入 (SQLite → PostgreSQL)**
   - 高速検索
   - 統計クエリ

9. **🗺️ 複数バンド表示**
   - RGB / 近赤外 / NDVI 切替
   - 植生・水域の可視化

10. **📱 PWA (Progressive Web App) 対応**
    - ホーム画面に追加可能
    - オフライン表示 (最終取得画像をキャッシュ)

---

## ライセンス

MIT License

衛星データ: Copernicus Sentinel-2 (© ESA, 利用規約: https://sentinel.esa.int/web/sentinel/terms-conditions)

地図データ: OpenStreetMap Contributors (© ODbL), CartoDB
