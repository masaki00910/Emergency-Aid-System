FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# 共有モジュールをコピー (相対パスでコピー)
COPY ../shared ./shared

# 共有モジュールのパスを設定
ENV PYTHONPATH=/app:/app/..

# ポート設定
EXPOSE 8082

# エントリーポイント
CMD ["python3", "minimal_faq_server.py"]