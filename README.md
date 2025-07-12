# 音声アシスタント「ルクス」

音声でGemini AIと対話できる日本語音声アシスタントシステムです。ウェイクワード「ルクス」で起動し、自然な日本語での質問応答が可能です。

## ✨ 主な機能

- 🎤 **ウェイクワード検知**: 「ルクス」で即座にアシスタント起動
- 🗣️ **日本語音声認識**: Google Speech Recognition API使用
- 🤖 **Gemini AI連携**: 自然言語での質問応答
- 🔊 **高品質音声出力**: Windows Speech APIによる日本語読み上げ
- ⚙️ **柔軟な設定管理**: JSON設定ファイルによるカスタマイズ
- 📝 **詳細ログ機能**: セッション記録とシステムログ

## 🚀 動作フロー

```
「ルクス、今日の天気は？」
    ↓
ウェイクワード検知 → 音声認識 → Gemini AI → 音声応答
    ↓
「今日の東京の天気は晴れ、気温は25℃です」（音声で回答）
```

## 📋 実装済み機能

### 🎤 音声入力・認識
- **ウェイクワード検知**: 「ルクス」「るくす」「Lux」等でアシスタント起動
- **同時コマンド認識**: 「ルクス、今日の天気は？」のように一度に認識
- **日本語音声認識**: Google Speech Recognition API使用
- **音声品質制御**: 16kHz、モノラル録音で高精度認識

### 🤖 Gemini AI連携
- **Gemini CLI統合**: Windows環境でgemini.cmd/geminiを自動検出
- **自然言語処理**: 天気、計算、雑談など幅広い質問に対応
- **エラーハンドリング**: タイムアウト、接続エラーに自動対応
- **レスポンス最適化**: 音声読み上げに適した応答形式

### 🔊 音声出力
- **Windows Speech API**: 高品質な日本語音声合成
- **ノイズ除去**: MCP STDERRやログ情報を自動除去
- **音声設定**: 速度・音量・音声の選択可能
- **同期/非同期再生**: 用途に応じた再生方式

### ⚙️ システム管理
- **JSON設定管理**: config.jsonで全設定を一元管理
- **セッションログ**: タイムスタンプ付き詳細記録
- **エラートラッキング**: システムエラーの詳細記録
- **動的設定変更**: 実行時の設定値変更対応

## 🚀 最新の最適化機能

### 📈 音声活動検出（VAD）による性能向上
**問題**: 従来の固定時間録音（10秒）がボトルネックとなり、平均処理時間が10秒超
**解決**: VAD（Voice Activity Detection）を実装し、発話終了を自動検出

#### 🎯 主な改善点
- **大幅な時間短縮**: 固定10秒 → 実際の発話時間（通常1-3秒）で自動終了
- **リアルタイム音声検出**: 音量レベルによる発話開始・終了の自動判定
- **設定可能なパラメータ**: 感度、無音判定時間、最小録音時間を調整可能

#### ⚙️ VAD設定パラメータ
```json
"vad_settings": {
    "max_duration": 5,           // 最大録音時間（秒）
    "silence_threshold": 0.005,  // 無音判定の閾値
    "min_duration": 0.3,         // 最小録音時間（秒）
    "post_silence_duration": 0.8, // 発話終了判定時間（秒）
    "chunk_duration": 0.1        // 音声チャンクの処理間隔（秒）
}
```

#### 🧪 性能テスト
VAD最適化の効果を検証するためのテストスクリプトを提供：
```bash
python test_vad_optimization.py
```

#### 📊 期待される改善
- **応答速度**: 60-80%の高速化（10秒 → 2-4秒）
- **ユーザー体験**: 自然な会話フロー
- **システム効率**: CPUとメモリ使用量の削減

## 🛠️ 技術スタック

### 使用技術
- **Python**: 3.8以上
- **音声処理**: pyaudio, speech_recognition
- **音声合成**: Windows Speech API (pyttsx3, win32com.client)
- **AI連携**: Gemini CLI (subprocess)
- **設定管理**: JSON
- **ログ管理**: Python logging

### 主要ライブラリ
```
pyaudio==0.2.14          # 音声入力
speech_recognition==3.11.0  # 音声認識
pyttsx3==2.97            # 音声合成
pywin32==308             # Windows Speech API
numpy==1.26.4            # 音声データ処理
```

## 📁 プロジェクト構成

```
c:\WorkFolders\dev\assistant\
├── main.py                    # メインアプリケーション
├── config.json               # 設定ファイル
├── requirements.txt          # 依存ライブラリ
├── README.md                 # このファイル
├── FINAL_REPORT.md          # 実装完了レポート
├── src/                     # ソースコードモジュール
│   ├── __init__.py
│   ├── audio_input.py        # 音声入力モジュール
│   ├── speech_recognition.py # 音声認識モジュール
│   ├── gemini_client.py      # Gemini CLI連携
│   ├── audio_output.py       # 音声出力モジュール
│   ├── config_manager.py     # 設定管理
│   └── logger.py             # ログ管理
└── logs/                     # ログディレクトリ
    └── session_*.log         # セッションログ
```

## ⚙️ 設定ファイル (config.json)

システムの動作は`config.json`で細かくカスタマイズできます：

```json
{
  "wake_words": ["ルクス", "るくす", "Lux", "lux", "LUX"],
  "exit_commands": ["終了", "しゅうりょう", "バイバイ", "ばいばい", "exit", "quit"],
  "audio_input": {
    "sample_rate": 16000,
    "channels": 1,
    "recording_duration": 5,
    "microphone_timeout": 30,
    "phrase_timeout": 5
  },
  "audio_output": {
    "rate": 180,
    "volume": 0.8,
    "voice_id": null,
    "max_text_length": 500
  },
  "gemini": {
    "model": "gemini-2.5-flash",
    "timeout": 30,
    "debug": false,
    "retry_count": 2
  },
  "system": {
    "log_level": "INFO",
    "startup_message": "音声アシスタント ルクス が起動しました。ルクス と呼びかけてください。",
    "shutdown_message": "音声アシスタントを終了します。お疲れ様でした。",
    "ready_message": "はい、何でしょうか？"
  },
  "vad_settings": {
    "max_duration": 5,
    "silence_threshold": 0.005,
    "min_duration": 0.3,
    "post_silence_duration": 0.8,
    "chunk_duration": 0.1
  }
}
```

## 🚀 セットアップ・実行方法

### 必要な前提条件
- **Python 3.8以上**
- **Gemini CLI**のインストールと設定
- **マイクとスピーカー**が利用可能な環境
- **インターネット接続**（音声認識・Gemini API使用時）

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd assistant
```

### 2. 依存関係のインストール
```bash
# 必要なライブラリをインストール
pip install -r requirements.txt

# インストール確認
python -c "import pyaudio, speech_recognition, pyttsx3; print('✅ 全ライブラリ正常')"
```

### 3. Gemini CLIの確認
```bash
# Gemini CLIが利用可能か確認
gemini --version

# テスト実行
gemini -p "こんにちは"
```

### 4. システム起動
```bash
# 音声アシスタント起動
python main.py
```

### 動作確認
1. 起動音声「音声アシスタント ルクス が起動しました...」が聞こえる
2. 「ルクス、今日の天気は？」などと話しかける
3. Geminiからの応答が音声で返される
4. 「終了」と言うか、Ctrl+Cで終了

## 🎯 使用例

```
ユーザー: 「ルクス、今日の東京の天気を教えて」
ルクス  : 「今日の東京の天気は晴れ、気温は25℃です。」

ユーザー: 「ルクス、3掛ける7は？」  
ルクス  : 「3掛ける7は21です。」

ユーザー: 「ルクス、終了」
ルクス  : 「音声アシスタントを終了します。お疲れ様でした。」
```

## 🔧 トラブルシューティング

### PyAudioエラーの場合
```bash
# PyAudioをインストール
pip install PyAudio

# インストール確認
python -c "import pyaudio; print('PyAudio OK')"
```

### 音声が聞こえない場合
1. Windows音量設定の確認
2. スピーカー/ヘッドフォンの接続確認
3. `config.json`の`audio_output.volume`を1.0に設定

### マイクが認識されない場合
1. マイクの接続とプライバシー設定の確認
2. 他のアプリでマイクが使用されていないか確認
3. PyAudioの再インストール: `pip uninstall pyaudio && pip install pyaudio`

### Gemini CLIエラーの場合
1. Gemini CLIの再インストール
2. API認証の確認
3. インターネット接続の確認

### 音声認識精度の向上
1. 静かな環境での使用
2. マイクを口に近づける
3. はっきりとした発音

## 📝 開発情報

### ログの確認
```bash
# セッションログの確認
ls logs/
cat logs/session_*.log
```

### 設定のカスタマイズ
- ウェイクワードの追加: `config.json`の`wake_words`配列に追加
- 音声速度の調整: `audio_output.rate`を変更（100-300推奨）
- タイムアウト時間: `gemini.timeout`や`audio_input.microphone_timeout`を調整
- **Geminiモデル変更**: `gemini.model`を変更（例: "gemini-2.5-pro", "gemini-2.5-flash"）

## 📄 ライセンス

MIT License - 詳細はLICENSEファイルを参照

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesまでお願いします。
