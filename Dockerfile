# Pythonの公式イメージをベースにする
FROM python:3.11-slim

# OSパッケージを更新し、ffmpegをインストール
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 必要なPythonライブラリをインストール
# yt-dlpはyt-dlp-cli-serverの実行に必要
COPY pyproject.toml /app/
COPY poetry.lock /app/
WORKDIR /app
RUN pip install poetry && poetry install --no-root

# サーバーコードをコピー (あなたのPythonコードがここにあると仮定)
COPY your_server_file.py /app/
COPY your_server_file.py /app/ # Flask/FastAPIなどのメインファイル

# 環境変数PORTでサーバーを起動
CMD ["poetry", "run", "gunicorn", "your_server_file:app", "-b", "0.0.0.0:$PORT"]
