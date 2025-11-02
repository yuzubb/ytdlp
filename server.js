// server.js

const express = require('express');
const { execFile } = require('child_process'); // 子プロセス実行のためのモジュール
const util = require('util');
const execFilePromise = util.promisify(execFile);

const app = express();
app.use(express.json()); // JSON形式のリクエストボディを解析

// Renderが指定する環境変数PORTを読み込む
const PORT = process.env.PORT || 3000;

// ==========================================================
// ルートエンドポイント
// ==========================================================
app.get('/', (req, res) => {
  res.send('Welcome to the yt-dlp server. Use POST /info with a URL to get video data.');
});


// ==========================================================
// yt-dlp 実行エンドポイント
// ==========================================================
app.post('/info', async (req, res) => {
  const videoUrl = req.body.url;

  if (!videoUrl) {
    return res.status(400).json({ error: 'URL is required in the request body.' });
  }

  // セキュリティ対策: URLの検証（最低限の確認）
  if (!videoUrl.startsWith('http')) {
    return res.status(400).json({ error: 'Invalid URL format.' });
  }

  // yt-dlp コマンドと引数
  const command = 'yt-dlp';
  // --dump-json: 動画のメタデータをJSON形式で出力
  const args = ['--dump-json', '--', videoUrl]; 

  try {
    // yt-dlpを実行
    const { stdout } = await execFilePromise(command, args, { 
        timeout: 20000, // タイムアウト20秒
        maxBuffer: 1024 * 1024 * 10 // 最大バッファサイズ10MB
    });

    // 出力されたJSON文字列をパース
    const videoData = JSON.parse(stdout);
    
    // クライアントに動画情報を返却
    res.json({
      success: true,
      title: videoData.title,
      uploader: videoData.uploader,
      duration: videoData.duration,
      view_count: videoData.view_count,
      formats_count: videoData.formats.length,
      full_data: videoData // 全体のデータも確認のために含める
    });

  } catch (error) {
    console.error(`yt-dlp execution failed: ${error.message}`);
    // yt-dlpの実行エラーをクライアントに通知
    res.status(500).json({ 
      success: false, 
      error: 'Failed to retrieve video information.',
      details: error.message 
    });
  }
});


// サーバーを起動
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
  console.log(`Access the server at: http://localhost:${PORT}`);
});
