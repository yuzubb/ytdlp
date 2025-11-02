# main.py

import os
import json
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # CORSを追加

# FastAPIアプリケーションのインスタンス化
app = FastAPI()

# ⚠️ CORS設定の追加
# これにより、任意のWebページからこのAPIを呼び出せるようになります。
origins = ["*"] # 本番環境では特定のドメインに限定することを推奨

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストボディの型定義 (このファイル内では未使用になりましたが、残しておきます)
class URLRequest(BaseModel):
    url: str

# ==========================================================
# ルートエンドポイント (変更なし)
# ==========================================================
@app.get("/")
def read_root():
    return {"message": "Welcome to yt-dlp FastAPI server on Render. Use /stream/{videoid} for stream URLs."}

# ==========================================================
# 新しいストリーム取得エンドポイント
# ==========================================================
@app.get("/stream/{videoid}")
async def get_stream_url_by_id(videoid: str):
    # YouTubeのIDから完全なURLを構築
    video_url = f"https://www.youtube.com/watch?v={videoid}"

    # yt-dlp コマンドと引数
    # -f 'best[ext=mp4]/best'：最も品質の良いMP4フォーマット、または最良のフォーマットを選択
    # --get-url：動画のストリームURLのみを出力
    command = [
        "yt-dlp",
        "-f", "best[ext=mp4]/best",
        "--get-url",
        video_url
    ]

    try:
        # コマンドを実行し、標準出力をキャプチャ
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30 # タイムアウトを30秒に設定
        )

        # 標準出力からストリームURLを取得
        stream_url = result.stdout.strip()

        if not stream_url:
            raise Exception("yt-dlp returned no stream URL. (Video may be restricted or deleted)")

        # クライアントにストリームURLを返却
        return {
            "success": True,
            "videoid": videoid,
            "stream_url": stream_url
        }

    except subprocess.CalledProcessError as e:
        error_detail = e.stderr.strip().split('\n')[-1]
        raise HTTPException(status_code=500, detail=f"yt-dlp execution failed: {error_detail}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="yt-dlp execution timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# ==========================================================
# 既存の /info エンドポイント (メタデータ取得)
# /streamエンドポイントと機能が重複するため、必要なければ削除を推奨
# ==========================================================
@app.post("/info")
async def get_video_info(request: URLRequest):
    # 既存の/infoロジック...
    video_url = request.url
    command = ["yt-dlp", "--dump-json", "--no-warnings", video_url]
    # ... (try-exceptブロックは省略、上記コードと同じ)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True, 
            timeout=30
        )
        video_data = json.loads(result.stdout)
        return {
            "success": True,
            "title": video_data.get("title"),
            "uploader": video_data.get("uploader"),
            "duration_sec": video_data.get("duration"),
            "full_data_keys": list(video_data.keys())
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"yt-dlp execution failed: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="yt-dlp execution timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# ==========================================================
# ポートの設定（Render専用） (変更なし)
# ==========================================================
port = int(os.environ.get("PORT", 8000))

# ローカルテスト用のエントリポイント（Renderでは使用されない）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
