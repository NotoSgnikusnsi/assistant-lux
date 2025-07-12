# 音声アシスタント「ルクス」(Lux)

音声でGemini AIと対話できる**次世代日本語音声アシスタントシステム**です。ウェイクワード「ルクス」で起動し、自然な日本語での質問応答が可能です。高度な音声最適化機能と常時監視システムにより、快適な音声対話体験を提供します。

## ✨ 主な機能

- 🎤 **常時ウェイクワード監視**: 「ルクス」で即座にアシスタント起動
- 🗣️ **高精度音声認識**: Google Speech Recognition + 音韻的検証
- 🤖 **Gemini AI連携**: 自然言語での質問応答（gemini-2.5-flash対応）
- 🔊 **高品質音声出力**: Windows Speech API + 音声キャッシュ
- ⚙️ **インテリジェント設定管理**: JSON設定 + パフォーマンス自動最適化
- � **リアルタイム性能監視**: 詳細パフォーマンス統計とボトルネック分析
- 🎛️ **動的音声品質調整**: 使用状況に応じた品質プロファイル自動切替

## 🚀 動作フロー

```
「ルクス、今日の天気は？」
    ↓
常時監視 → ウェイクワード検知 → 音韻的検証 → VAD音声認識 → Gemini AI → キャッシュ音声出力
    ↓
「今日の東京の天気は晴れ、気温は25℃です」（高品質音声で即座に回答）
```

## 📋 実装済み機能

### 🎤 音声入力・認識システム
- **常時ウェイクワード監視**: 「ルクス」「るくす」「Lux」等を24時間監視
- **同時コマンド抽出**: 「ルクス、今日の天気は？」のように一度に認識
- **VAD（音声活動検出）**: 発話終了を自動検知し、大幅な応答時間短縮
- **音韻的検証システム**: 類似音での誤検知を防ぐ高度なフィルタリング
- **並列音声認識**: 複数エンジンによる認識精度向上
- **動的品質調整**: ウェイクワード/コマンド/会話用の自動品質切替

### 🤖 Gemini AI連携
- **Gemini CLI統合**: Windows環境でgemini.cmd/geminiを自動検出
- **高速通信**: 最適化されたプロンプト送信で応答時間短縮
- **自然言語処理**: 天気、計算、雑談など幅広い質問に対応
- **エラーハンドリング**: タイムアウト、接続エラーに自動対応
- **モデル選択**: gemini-2.5-flash/pro等のモデル切替対応

### 🔊 音声出力システム
- **Windows Speech API**: 高品質な日本語音声合成
- **音声キャッシュ**: よく使用されるフレーズの事前生成・高速再生
- **ノイズ除去**: MCP STDERR、ログ情報、制御文字の自動除去
- **音声設定**: 速度・音量・音声の選択可能
- **非同期再生**: ブロッキングなしの音声出力

### ⚙️ システム管理・最適化
- **パフォーマンス監視**: リアルタイムでの処理時間測定と統計
- **自動最適化**: ボトルネックの自動検出と設定提案
- **重複防止**: コマンド・ウェイクワードのクールダウン機能
- **JSON設定管理**: config.jsonで全設定を一元管理
- **セッションログ**: タイムスタンプ付き詳細記録
- **統計レポート**: 音声認識成功率、処理時間等の詳細分析

## 🚀 最新の最適化機能

### 📈 VAD（音声活動検出）による革新的な性能向上
**課題**: 従来の固定時間録音（5-10秒）によるユーザー体験の悪化と応答遅延
**解決**: 発話終了を自動検知するVADシステムの実装

#### 🎯 主な改善点
- **劇的な時間短縮**: 固定5-10秒 → 実際の発話時間（通常1-3秒）で自動終了
- **リアルタイム音声検出**: 音量レベルによる発話開始・終了の精密な自動判定
- **インテリジェント設定**: 環境に応じた感度・閾値の自動調整

#### ⚙️ VAD設定パラメータ
```json
"vad_settings": {
    "max_duration": 5,           // 最大録音時間（秒）
    "silence_threshold": 0.005,  // 無音判定の閾値
    "min_duration": 0.3,         // 最小録音時間（秒）
    "post_silence_duration": 0.8, // 発話終了判定時間（秒）
    "chunk_duration": 0.1        // 音声チャンク処理間隔（秒）
}
```

### 🧠 音韻的検証システム（誤検知防止）
**課題**: 「ラックス」「クス」等の類似音でのウェイクワード誤検知
**解決**: 日本語音韻学に基づく高度な検証アルゴリズム

#### 🔬 検証機能
- **多層アルゴリズム**: 編集距離・音韻パターン・部分文字列マッチング
- **早期終了最適化**: 高信頼度検知時の処理時間短縮（10ms以下）
- **動的閾値調整**: 使用環境に応じた検証精度の自動調整

### 📊 リアルタイムパフォーマンス監視
**機能**: 全処理ステップの詳細測定と統計分析

#### 🔍 監視項目
- **音声入力時間**: VAD処理とマイク録音時間
- **音声認識時間**: Google Speech API応答時間
- **Gemini通信時間**: プロンプト送信～応答受信
- **音声出力時間**: TTS合成と再生時間
- **総応答時間**: ウェイクワード検知～音声出力完了

#### 📈 統計機能
```bash
# 統計表示コマンド
「ルクス、統計」または「ルクス、パフォーマンス」

# 自動最適化コマンド
「ルクス、最適化」または「ルクス、高速化」
```

### 🎛️ 動的音声品質調整システム
**機能**: 使用状況に応じた音声品質の自動最適化

#### 📋 品質プロファイル
```json
"quality_profiles": {
    "wake_word": {      // ウェイクワード検知用（高速・低品質）
        "sample_rate": 8000,
        "chunk_size": 256
    },
    "command": {        // コマンド認識用（標準品質）
        "sample_rate": 11025,
        "chunk_size": 512
    },
    "conversation": {   // 会話用（高品質）
        "sample_rate": 16000,
        "chunk_size": 1024
    }
}
```

### 🔄 並列音声認識システム
**機能**: 複数認識エンジンによる精度向上と高速化

#### 🏃‍♂️ 並列処理機能
- **非同期認識**: 複数のSpeech Recognition APIを並列実行
- **最速結果採用**: 最初に成功した結果を即座に採用
- **フェイルオーバー**: 主認識エンジン失敗時の自動切替

### 🎵 音声キャッシュシステム
**機能**: よく使用されるフレーズの事前生成と高速再生

#### 📦 キャッシュ対象
```json
"cache_phrases": [
    "はい、何でしょうか？",
    "承知いたしました",
    "照明をつけました",
    "照明を消しました",
    "温度を設定しました",
    "申し訳ありません",
    "エラーが発生しました"
]
```

### ⚡ 重複処理防止システム
**機能**: 同じコマンドの重複実行を防ぐインテリジェントなクールダウン

#### 🛡️ 防止機能
```json
"duplicate_prevention": {
    "command_cooldown": 2.0,              // コマンド重複防止時間
    "wake_word_cooldown": 3.0,            // ウェイクワード重複防止時間
    "audio_output_suppression_time": 2.0  // 音声出力中の検知抑制時間
}
```

#### 🧪 性能テスト・検証
各最適化機能の効果を検証するテストスクリプトを提供：
```bash
python test_vad_optimization.py          # VAD最適化テスト
python test_phonetic_verification.py     # 音韻的検証テスト  
python test_performance.py               # 総合性能テスト
python test_optimization.py              # 自動最適化テスト
```

#### 📊 期待される改善効果
- **応答速度**: 60-80%の高速化（5-10秒 → 2-4秒）
- **認識精度**: 誤検知率90%削減
- **ユーザー体験**: 自然な会話フローの実現
- **システム効率**: CPU・メモリ使用量の最適化

## 🛠️ 技術スタック

### 使用技術
- **Python**: 3.8以上（型ヒント・async/await対応）
- **音声処理**: pyaudio, speech_recognition, webrtcvad
- **音声合成**: Windows Speech API (pyttsx3, win32com.client)
- **AI連携**: Gemini CLI (subprocess)
- **設定管理**: JSON + 動的リロード
- **ログ管理**: Python logging + セッション管理
- **並列処理**: concurrent.futures, threading
- **パフォーマンス**: dataclasses, statistics

### 主要ライブラリ
```
# 必須ライブラリ
pyaudio>=0.2.14                # 音声入力
speech_recognition>=3.10.0     # 音声認識
pyttsx3>=2.90                  # 音声合成
pywin32>=308                   # Windows Speech API
numpy>=1.24.0                  # 音声データ処理
webrtcvad>=2.0.10              # 音声活動検知

# 最適化ライブラリ
pygame>=2.1.0                  # キャッシュ音声再生（オプション）
unicodedata2>=15.0.0           # Unicode正規化（オプション）
```

### アーキテクチャ特徴
- **モジュラー設計**: 各機能を独立したモジュールとして実装
- **非同期処理**: ブロッキングなしの並列音声処理
- **リアルタイム監視**: 常時音声監視とパフォーマンス測定
- **自動最適化**: 使用状況に応じた設定の動的調整
- **拡張性**: プラグイン式の認識エンジン追加対応

## 📁 プロジェクト構成

```
c:\WorkFolders\dev\assistant\
├── main.py                     # メインアプリケーション
├── config.json                # 設定ファイル
├── requirements.txt           # 依存ライブラリ
├── README.md                  # このファイル
├── FINAL_REPORT.md           # 実装完了レポート
├── PHONETIC_VERIFICATION_GUIDE.md  # 音韻的検証ガイド
├── VAD_OPTIMIZATION_REPORT.md      # VAD最適化レポート
├── INTEGRATION_COMPLETION_REPORT.md # 統合完了レポート
├── src/                       # ソースコードモジュール
│   ├── __init__.py
│   ├── audio_input.py         # 音声入力・VAD処理
│   ├── speech_recognizer.py   # 音声認識・ウェイクワード検知
│   ├── continuous_speech.py   # 常時音声監視システム
│   ├── gemini_client.py       # Gemini CLI連携
│   ├── audio_output.py        # 音声出力・キャッシュ管理
│   ├── config_manager.py      # 設定管理・動的リロード
│   ├── logger.py              # ログ管理
│   ├── performance_monitor.py # パフォーマンス監視
│   ├── phonetic_similarity.py # 音韻的類似度計算
│   ├── parallel_speech.py     # 並列音声認識
│   ├── dynamic_audio.py       # 動的音声品質調整
│   └── audio_cache.py         # 音声キャッシュシステム
├── test_*.py                  # 各種テストスクリプト
├── logs/                      # ログディレクトリ
│   └── session_*.log          # セッションログ
└── cache/                     # キャッシュディレクトリ
    └── audio/                 # 音声キャッシュファイル
```

## ⚙️ 設定ファイル (config.json)

システムの動作は`config.json`で細かくカスタマイズできます：

### 🎤 音声入力・VAD設定
```json
{
  "audio_input": {
    "sample_rate": 16000,
    "channels": 1,
    "recording_duration": 3,
    "microphone_timeout": 30,
    "phrase_timeout": 5,
    "vad_enabled": true
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

### 🚀 音声最適化設定
```json
{
  "audio_optimization": {
    "parallel_recognition": true,
    "pregenerated_cache": true,
    "dynamic_quality": true,
    "duplicate_prevention": {
      "command_cooldown": 2.0,
      "wake_word_cooldown": 3.0,
      "audio_output_suppression_time": 2.0
    },
    "phonetic_verification": {
      "early_exit_threshold": 0.8,
      "short_text_threshold": 6,
      "max_processing_time_ms": 10.0,
      "enable_multi_algorithm": true
    }
  }
}
```

### 🎛️ 品質プロファイル設定
```json
{
  "quality_profiles": {
    "wake_word": {
      "sample_rate": 8000,
      "chunk_size": 256
    },
    "command": {
      "sample_rate": 11025,
      "chunk_size": 512
    },
    "conversation": {
      "sample_rate": 16000,
      "chunk_size": 1024
    }
  }
}
```

### 🤖 Gemini AI設定
```json
{
  "gemini": {
    "model": "gemini-2.5-flash",
    "timeout": 15,
    "optimized_timeout": 15,
    "enable_optimization": true,
    "debug": false,
    "retry_count": 1
  }
}
```

### 🔊 音声出力設定
```json
{
  "audio_output": {
    "rate": 200,
    "volume": 0.8,
    "voice_id": null,
    "max_text_length": 200,
    "force_windows_speech": true,
    "async_output": true
  }
}
```

### 🎯 ウェイクワード・コマンド設定
```json
{
  "wake_words": [
    "ルクス", "るくす", "ルークス", "るーくす", "Lux", "lux", "LUX"
  ],
  "exit_commands": [
    "終了", "しゅうりょう", "バイバイ", "ばいばい", "exit", "quit"
  ],
  "performance_commands": [
    "統計", "とうけい", "パフォーマンス", "ぱふぉーまんす", "performance", "stats"
  ],
  "optimization_commands": [
    "最適化", "さいてきか", "高速化", "こうそくか", "optimize", "speed up"
  ]
}
```

## 🚀 セットアップ・実行方法

### 必要な前提条件
- **Python 3.8以上**
- **Gemini CLI**のインストールと設定
- **マイクとスピーカー**が利用可能な環境
- **インターネット接続**（音声認識・Gemini API使用時）
- **Windows OS**（Windows Speech API使用）

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
python -c "import pyaudio, speech_recognition, pyttsx3, webrtcvad; print('✅ 全ライブラリ正常')"
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
2. 常時ウェイクワード監視が開始される
3. 「ルクス、今日の天気は？」などと話しかける
4. Geminiからの応答が音声で返される
5. 「終了」と言うか、Ctrl+Cで終了

## 🎯 使用例

### 基本的な対話
```
ユーザー: 「ルクス、今日の東京の天気を教えて」
ルクス  : 「今日の東京の天気は晴れ、気温は25℃です。」

ユーザー: 「ルクス、3掛ける7は？」  
ルクス  : 「3掛ける7は21です。」

ユーザー: 「ルクス、終了」
ルクス  : 「音声アシスタントを終了します。お疲れ様でした。」
```

### システム管理コマンド
```
# パフォーマンス統計の確認
ユーザー: 「ルクス、統計」
ルクス  : 「パフォーマンス統計を表示しました。詳細はコンソールをご確認ください。」

# 自動最適化の実行
ユーザー: 「ルクス、最適化」  
ルクス  : 「システム最適化を完了しました。3項目の設定を更新しました。」
```

### 高度な機能
```
# 同時コマンド認識
ユーザー: 「ルクス、明日の予定を教えて」
→ ウェイクワードとコマンドを同時に認識・処理

# 音韻的検証による誤検知防止
「ラックス」「クス」→ 誤検知されずに無視
「ルクス」→ 正確に検知・応答
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### PyAudioエラーの場合
```bash
# PyAudioをインストール
pip install PyAudio

# インストール確認
python -c "import pyaudio; print('PyAudio OK')"

# Windows環境でのエラーの場合
pip install pipwin
pipwin install pyaudio
```

#### webrtcvadエラーの場合
```bash
# webrtcvadインストール（VAD機能用）
pip install webrtcvad

# インストール確認
python -c "import webrtcvad; print('webrtcvad OK')"
```

#### 音声が聞こえない場合
1. **Windows音量設定の確認**
2. **スピーカー/ヘッドフォンの接続確認**
3. **config.jsonの音量設定**を1.0に変更:
   ```json
   "audio_output": {
     "volume": 1.0
   }
   ```
4. **Windows Speech APIの確認**:
   ```bash
   python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('テスト'); engine.runAndWait()"
   ```

#### マイクが認識されない場合
1. **マイクの接続とプライバシー設定の確認**
2. **他のアプリでマイクが使用されていないか確認**
3. **利用可能なマイクデバイス確認**:
   ```bash
   python -c "
   import pyaudio
   p = pyaudio.PyAudio()
   for i in range(p.get_device_count()):
       print(p.get_device_info_by_index(i))
   p.terminate()
   "
   ```
4. **PyAudioの再インストール**: `pip uninstall pyaudio && pip install pyaudio`

#### Gemini CLIエラーの場合
1. **Gemini CLIの再インストール**
2. **API認証の確認**:
   ```bash
   gemini config set api_key YOUR_API_KEY
   ```
3. **インターネット接続の確認**
4. **プロキシ設定の確認**（企業環境の場合）

#### パフォーマンスが遅い場合
1. **VAD設定の調整**:
   ```json
   "vad_settings": {
     "silence_threshold": 0.01,  // より敏感に
     "post_silence_duration": 0.5  // より短く
   }
   ```
2. **Geminiタイムアウトの調整**:
   ```json
   "gemini": {
     "timeout": 10,  // より短く
     "optimized_timeout": 10
   }
   ```
3. **音声品質の調整**:
   ```json
   "audio_input": {
     "sample_rate": 8000  // より低品質・高速
   }
   ```

#### 音声認識精度の向上
1. **静かな環境での使用**
2. **マイクを口に近づける（15-30cm推奨）**
3. **はっきりとした発音**
4. **ノイズキャンセリング機能付きマイクの使用**
5. **VAD感度の調整**:
   ```json
   "vad_settings": {
     "silence_threshold": 0.003  // より敏感に
   }
   ```

#### ウェイクワード誤検知の解決
1. **音韻的検証の有効化確認**:
   ```json
   "audio_optimization": {
     "phonetic_verification": {
       "enable_multi_algorithm": true
     }
   }
   ```
2. **検証閾値の調整**:
   ```json
   "phonetic_verification": {
     "early_exit_threshold": 0.9  // より厳格に
   }
   ```

### ログ確認方法
```bash
# 最新のセッションログ確認
ls logs/ | tail -1 | xargs -I {} cat logs/{}

# エラーログの検索
grep -i "error" logs/session_*.log

# パフォーマンス統計の確認
grep -i "performance" logs/session_*.log
```

### デバッグモード
```json
{
  "gemini": {
    "debug": true
  },
  "system": {
    "log_level": "DEBUG"
  }
}
```

## 📝 開発・カスタマイズ情報

### テストスクリプト
各機能を個別にテストできるスクリプトを提供：

```bash
# VAD最適化のテスト
python test_vad_optimization.py

# 音韻的検証のテスト
python test_phonetic_verification.py

# 並列音声認識のテスト
python test_optimization.py

# パフォーマンス総合テスト
python test_performance.py

# ウェイクワード認識テスト
python test_lux_recognition.py

# 重複防止機能テスト
python test_duplicate_prevention.py

# 動的品質調整テスト
python test_optimized_performance.py
```

### ログの確認
```bash
# セッションログの確認
ls logs/
cat logs/session_*.log

# リアルタイムログ監視
tail -f logs/session_$(date +%Y%m%d_*)*.log
```

### 設定のカスタマイズ
- **ウェイクワードの追加**: `config.json`の`wake_words`配列に追加
  ```json
  "wake_words": ["ルクス", "るくす", "Lux", "アシスタント", "AI"]
  ```
- **音声速度の調整**: `audio_output.rate`を変更（100-300推奨）
  ```json
  "audio_output": { "rate": 250 }
  ```
- **タイムアウト時間**: 各種timeout設定を調整
  ```json
  "gemini": { "timeout": 20 },
  "audio_input": { "microphone_timeout": 45 }
  ```
- **Geminiモデル変更**: より高性能なモデルを選択
  ```json
  "gemini": { "model": "gemini-2.5-pro" }
  ```

### 拡張機能の追加
プロジェクトは拡張しやすい設計になっています：

1. **新しい音声認識エンジンの追加**:
   ```python
   # src/speech_recognizer.py に新しいエンジンを追加
   def recognize_with_whisper(self, audio_data):
       # Whisper実装
   ```

2. **カスタムウェイクワード検証**:
   ```python
   # src/phonetic_similarity.py に新しいアルゴリズムを追加
   def custom_verification_algorithm(self, text):
       # カスタム検証ロジック
   ```

3. **新しい音声出力エンジン**:
   ```python
   # src/audio_output.py に新しいエンジンを追加
   def speak_with_custom_tts(self, text):
       # カスタムTTS実装
   ```

### パフォーマンス最適化
システムが自動で最適化を提案しますが、手動でも調整可能：

```json
{
  "audio_optimization": {
    "parallel_recognition": true,     // 並列音声認識
    "pregenerated_cache": true,       // 音声キャッシュ
    "dynamic_quality": true,          // 動的品質調整
    "duplicate_prevention": {...}     // 重複防止
  }
}
```

### APIドキュメント
主要クラスの使用方法：

```python
# 音声アシスタントの基本的な使用
from main import VoiceAssistant
assistant = VoiceAssistant("config.json")
assistant.run()

# 個別コンポーネントの使用
from src.speech_recognizer import SpeechRecognizer
recognizer = SpeechRecognizer("ja-JP")
text = recognizer.recognize_from_microphone()

# パフォーマンス監視
from src.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
session_id = monitor.start_session("テスト")
# ... 処理 ...
monitor.finish_session(True)
```

## � システム仕様・性能指標

### 処理性能目標値
- **ウェイクワード検知**: < 0.5秒
- **音声認識**: < 2秒（VAD使用時）
- **Gemini通信**: < 3秒（gemini-2.5-flash使用時）
- **音声出力**: < 1秒（キャッシュヒット時）
- **総応答時間**: < 6秒（ウェイクワード検知～音声出力完了）

### システム要件
- **CPU**: Intel Core i3以上 または AMD同等品
- **メモリ**: 4GB以上（8GB推奨）
- **ストレージ**: 500MB以上の空き容量
- **ネットワーク**: インターネット接続（音声認識・Gemini API用）
- **OS**: Windows 10/11（Windows Speech API必須）
- **音声デバイス**: マイク・スピーカー対応

### サポートされている機能
- ✅ **音声認識言語**: 日本語（ja-JP）、英語（en-US）
- ✅ **Geminiモデル**: gemini-2.5-flash, gemini-2.5-pro
- ✅ **音声形式**: 16kHz/8kHz/11kHz、モノラル、16bit
- ✅ **ウェイクワード**: カスタマイズ可能（デフォルト: ルクス）
- ✅ **音声出力**: Windows SAPI、音声キャッシュ対応
- ✅ **並列処理**: 最大4スレッドまでの並列音声認識

### 制限事項
- ❌ **macOS/Linux**: Windows Speech API依存のため非対応
- ❌ **オフライン動作**: インターネット接続必須
- ❌ **多言語同時認識**: 単一言語のみ対応
- ❌ **複数ユーザー**: 話者認識機能なし

## 🔄 更新履歴

### Version 2.0 - 2025年7月 (最新)
- 🎯 **常時ウェイクワード監視システム追加**
- 🧠 **音韻的検証による誤検知防止機能**
- 📈 **VAD（音声活動検出）による応答時間大幅短縮**
- 🔄 **並列音声認識システム実装**
- 🎛️ **動的音声品質調整機能**
- 📊 **リアルタイムパフォーマンス監視**
- 🎵 **音声キャッシュシステム**
- ⚡ **重複処理防止機能**
- 🚀 **自動最適化システム**

### Version 1.0 - 2025年7月
- 🎤 **基本的なウェイクワード検知**
- 🗣️ **音声認識・Gemini連携**
- 🔊 **音声出力・設定管理**
- 📝 **ログ機能・基本システム**

## �📄 ライセンス

MIT License - 詳細はLICENSEファイルを参照

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

### 開発ガイドライン
1. **コーディング規約**: PEP 8準拠
2. **型ヒント**: 必須（Python 3.8+）
3. **テスト**: 新機能には対応するテストスクリプトを追加
4. **ドキュメント**: docstring必須
5. **パフォーマンス**: 新機能はパフォーマンス監視対応

## 📞 サポート

### 問い合わせ
- **GitHub Issues**: バグ報告・機能要求
- **Discussions**: 使用方法・質問
- **Wiki**: 詳細なドキュメント

### よくある質問（FAQ）
1. **Q: ウェイクワードを変更できますか？**  
   A: はい、config.jsonのwake_wordsで設定可能です。

2. **Q: オフラインで使用できますか？**  
   A: いいえ、音声認識とGemini APIでインターネット接続が必要です。

3. **Q: 他の言語に対応していますか？**  
   A: 現在は日本語メインですが、config.jsonで英語等に変更可能です。

4. **Q: 応答が遅い場合の対処法は？**  
   A: 「ルクス、最適化」コマンドで自動最適化を実行してください。

5. **Q: 誤検知が多い場合は？**  
   A: 音韻的検証の閾値をconfig.jsonで調整してください。

---

**音声アシスタント「ルクス」で、未来の音声対話体験をお楽しみください！** 🚀
