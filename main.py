# main.py

import os
import json
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# FastAPIアプリケーションのインスタンス化
app = FastAPI()

# リクエストボディの型定義
class URLRequest(BaseModel):
    url: str

# ==========================================================
# ルートエンドポイント
# ==========================================================
@app.get("/")
def read_root():
    return {"message": "Welcome to yt-dlp FastAPI server on Render. Use POST /info to get data."}

# ==========================================================
# yt-dlp 実行エンドポイント
# ==========================================================
@app.post("/info")
async def get_video_info(request: URLRequest):
    video_url = request.url

    # yt-dlpの実行コマンド
    # --dump-json: メタデータをJSONで出力
    # --no-warnings: 警告を出力しない
    command = [
        "yt-dlp",
        "--dump-json",
        "--no-warnings",
        video_url
    ]

    try:
        # コマンドを実行し、標準出力をキャプチャ
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, # 0以外の終了コードで例外を発生させる
            timeout=30 # タイムアウトを30秒に設定
        )
        
        # 出力されたJSON文字列をパース
        video_data = json.loads(result.stdout)

        # 必要な情報を抽出して返却
        return {
            "success": True,
            "title": video_data.get("title"),
            "uploader": video_data.get("uploader"),
            "duration_sec": video_data.get("duration"),
            "full_data_keys": list(video_data.keys())
        }

    except subprocess.CalledProcessError as e:
        # yt-dlp自体がエラーコードを返した場合
        raise HTTPException(status_code=500, detail=f"yt-dlp execution failed: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        # 実行がタイムアウトした場合
        raise HTTPException(status_code=500, detail="yt-dlp execution timed out.")
    except Exception as e:
        # その他のエラー
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# ==========================================================
# ポートの設定（Render専用）
# ==========================================================
# Renderは環境変数PORTを設定するので、それを取得する
port = int(os.environ.get("PORT", 8000))

# ローカルテスト用のエントリポイント（Renderでは使用されない）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
