# 音声アシスタントシステム

マイクからの音声入力を処理し、Gemini AIで応答を生成して音声で出力する、音声対話アシスタントシステムです。

## システム概要

```
マイク → ウェイクワード検知 → 音声文字起こし → Gemini CLI → 結果を出力 → 出力内容をスピーカーで再生
```

## 機能仕様

### 1. 音声入力処理
- **マイク入力**: リアルタイムでマイクからの音声を監視
- **ウェイクワード検知**: 特定のキーワード（例：「アシスタント」「ヘイ、ジェミニ」など）を検知
- **音声録音**: ウェイクワード検知後、一定時間または無音検知まで音声を録音

### 2. 音声認識
- **音声文字起こし**: 録音した音声をテキストに変換
- **技術候補**: 
  - Google Speech-to-Text API
  - OpenAI Whisper
  - Windows Speech Recognition API

### 3. AI処理
- **Gemini CLI連携**: 文字起こしされたテキストをGemini CLIに送信
- **プロンプト処理**: 適切なプロンプトフォーマットで質問を送信
- **応答取得**: Geminiからの回答テキストを取得

### 4. 音声出力
- **テキスト読み上げ**: Geminiの応答テキストを音声に変換
- **スピーカー出力**: 生成された音声をスピーカーで再生
- **技術候補**:
  - Windows Speech Platform
  - Google Text-to-Speech API
  - Azure Cognitive Services Speech

## 技術構成

### プログラミング言語
- **Python**: 音声処理、AI連携に豊富なライブラリを活用

### 主要ライブラリ（確定版）

#### 音声入出力
- **`sounddevice`**: マイク入力/音声出力 
  - PyAudioより安定性が高く、Windowsでの動作が良好
  - リアルタイム音声処理に適している
- **`soundfile`**: 音声ファイルの読み書き
  - WAVファイルの操作、NumPy配列との連携が容易

#### 音声認識
- **`speech_recognition`**: 音声認識ライブラリ
  - 複数のエンジン（Google、Whisper等）をサポート
  - 使いやすいAPI、Windowsで安定動作
- **`openai-whisper`**: ローカル音声認識（オプション）
  - オフライン動作可能、高精度、日本語対応良好

#### 音声合成
- **`pyttsx3`**: テキスト読み上げ
  - Windows Speech APIを使用、オフライン動作
  - 簡単な設定で日本語対応
- **`gTTS`**: Google Text-to-Speech（オプション）
  - 高品質な音声合成、要インターネット接続

#### ウェイクワード検知
- **`pvporcupine`**: Porcupine Wake Word
  - 高精度なウェイクワード検知、リアルタイム処理
  - カスタムウェイクワード作成可能
- **`vosk`**: 軽量音声認識（代替案）
  - オフライン動作、軽量、リアルタイム対応

#### データ処理・制御
- **`numpy`**: 音声データの数値計算
- **`threading`**: 並行処理（標準ライブラリ）
- **`queue`**: スレッド間通信（標準ライブラリ）
- **`subprocess`**: Gemini CLI実行（標準ライブラリ）
- **`json`**: 設定ファイル管理（標準ライブラリ）
- **`logging`**: ログ出力（標準ライブラリ）

#### 設定・ユーティリティ
- **`python-dotenv`**: 環境変数管理
- **`configparser`**: 設定ファイル管理（標準ライブラリ）

## ライブラリ選定理由

### 音声処理
- **sounddevice**: PyAudioの代替として選定。Windowsでのドライバー問題が少なく、NumPyとの連携が良好
- **soundfile**: libsndfileベースで多様な音声フォーマットに対応、waveモジュールより高機能

### 音声認識
- **SpeechRecognition**: 統一APIで複数エンジンを切り替え可能、初心者にも使いやすい
- **Whisper**: 最高品質のローカル音声認識、プライバシー重視時に最適

### ウェイクワード検知
- **Porcupine**: 商用レベルの精度、カスタムウェイクワード作成可能（無料版は制限あり）
- **Vosk**: 完全オープンソース、軽量、オフライン動作

### 注意事項
- **Porcupine**: 商用利用時はライセンス要確認
- **Whisper**: 初回実行時にモデルダウンロード（数GB）
- **gTTS**: インターネット接続必須、利用制限あり

### システムフロー
```
1. マイク監視開始
2. ウェイクワード検知
3. 音声録音開始
4. 無音検知または制限時間で録音終了
5. 音声ファイルをテキスト変換
6. テキストをGemini CLIに送信
7. Gemini応答を取得
8. 応答テキストを音声合成
9. スピーカーで再生
10. 1に戻る
```

## 設定項目
- ウェイクワード設定
- 音声認識の言語設定（日本語/英語）
- 録音時間制限（デフォルト: 10秒）
- 音量調整
- Gemini CLIパス設定
- 無音検知閾値

## 実装手順

### Phase 1: 基本的な音声入出力機能
- [ ] **1.1 環境設定**
  - Python環境のセットアップ
  - 必要ライブラリのインストール
  - プロジェクト構造の作成

- [ ] **1.2 マイク入力機能**
  - PyAudioを使用したマイク音声の取得
  - 音声データのリアルタイム処理
  - 音声レベルの監視機能

- [ ] **1.3 音声出力機能**
  - pyttsx3を使用したテキスト読み上げ
  - 音声出力のテスト
  - 音量・速度調整機能

### Phase 2: 音声認識機能
- [ ] **2.1 音声録音機能**
  - 指定時間での音声録音
  - WAVファイルでの保存機能
  - 録音品質の調整

- [ ] **2.2 音声認識実装**
  - speech_recognitionライブラリの統合
  - Google Speech-to-Text APIの設定
  - 日本語音声認識のテスト

- [ ] **2.3 無音検知機能**
  - 音声レベルでの無音判定
  - 動的な録音終了機能
  - ノイズ対策

### Phase 3: ウェイクワード検知
- [ ] **3.1 簡易ウェイクワード検知**
  - キーワードマッチングによる検知
  - 音声認識結果からのキーワード抽出
  - 検知精度の調整

- [ ] **3.2 高度なウェイクワード検知（オプション）**
  - 機械学習モデルの導入
  - リアルタイム検知の最適化
  - 誤検知の削減

### Phase 4: Gemini CLI連携
- [ ] **4.1 Gemini CLI統合**
  - subprocessでのCLI実行
  - 入出力データの処理
  - エラーハンドリング

- [ ] **4.2 プロンプト最適化**
  - 音声アシスタント用プロンプトの作成
  - コンテキスト管理
  - 応答フォーマットの調整

### Phase 5: システム統合とテスト
- [ ] **5.1 全機能統合**
  - 各コンポーネントの統合
  - メインループの実装
  - 状態管理機能

- [ ] **5.2 設定管理**
  - 設定ファイル（JSON/YAML）の作成
  - 動的設定変更機能
  - デフォルト値の設定

- [ ] **5.3 エラーハンドリング**
  - 各段階でのエラー処理
  - ログ出力機能
  - 復旧処理の実装

- [ ] **5.4 最適化とテスト**
  - パフォーマンスの最適化
  - メモリ使用量の改善
  - 総合テストの実行

### Phase 6: 拡張機能（オプション）
- [ ] **6.1 GUI実装**
  - tkinterまたはPyQt5でのUI作成
  - 設定画面の実装
  - 状態表示機能

- [ ] **6.2 ログ・履歴機能**
  - 会話履歴の保存
  - ログファイルの管理
  - 統計情報の表示

## ファイル構成（予定）
```
assistant/
├── README.md
├── requirements.txt
├── config.json
├── main.py
├── src/
│   ├── __init__.py
│   ├── audio_input.py      # マイク入力・録音機能
│   ├── audio_output.py     # 音声出力機能
│   ├── speech_recognition.py  # 音声認識機能
│   ├── wake_word.py        # ウェイクワード検知
│   ├── gemini_client.py    # Gemini CLI連携
│   └── config_manager.py   # 設定管理
├── tests/
│   ├── test_audio.py
│   ├── test_speech.py
│   └── test_gemini.py
└── logs/
    └── assistant.log
```

## Gemini CLI連携の詳細

### プロンプト送信方法
Pythonから`subprocess`モジュールを使用してGemini CLIを実行します：

```bash
# 基本的な使用例
gemini -p "今日の東京の天気を教えて"
```

```python
import subprocess
import json

def send_to_gemini(prompt, model="gemini-2.5-pro", debug=False):
    """Gemini CLIにプロンプトを送信し、応答を取得"""
    try:
        # コマンドを構築
        cmd = ['gemini']
        
        # モデル指定
        if model:
            cmd.extend(['-m', model])
            
        # デバッグモード
        if debug:
            cmd.append('-d')
            
        # プロンプト指定
        cmd.extend(['-p', prompt])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise Exception(f"Gemini CLI error: {result.stderr}")
            
    except Exception as e:
        print(f"Error calling Gemini CLI: {e}")
        return None
```

### 設定オプション
Gemini CLIの主要なオプション：
- `-p, --prompt`: プロンプトを指定
- `-m, --model`: 使用するモデルを指定（デフォルト: "gemini-2.5-pro"）
- `-d, --debug`: デバッグモードで実行
- `-a, --all_files`: すべてのファイルをコンテキストに含める
- `-y, --yolo`: すべてのアクションを自動的に承認
- `-c, --checkpointing`: ファイル編集のチェックポイントを有効化
- `-s, --sandbox`: サンドボックスで実行
- `--show_memory_usage`: ステータスバーにメモリ使用量を表示

音声アシスタント用の推奨設定：
```python
# 基本的な設定（速度重視）
['gemini', '-p', prompt]

# デバッグ時の設定
['gemini', '-d', '-p', prompt]

# 特定のモデルを使用
['gemini', '-m', 'gemini-2.5-pro', '-p', prompt]
```

### プロンプト最適化例
```python
def create_assistant_prompt(user_input):
    """音声アシスタント用のプロンプトを作成"""
    system_prompt = """
あなたは音声アシスタントです。以下のルールに従って回答してください：
1. 簡潔で分かりやすい日本語で回答する
2. 音声で読み上げることを前提とした自然な文章にする  
3. 専門用語は避け、一般的な表現を使う
4. 応答は2-3文以内に収める
"""
    
    full_prompt = f"{system_prompt}\n\nユーザーの質問: {user_input}\n\n回答:"
    return full_prompt
```

## 必要な前提条件
- Python 3.8以上
- Gemini CLI のインストールと設定
- マイクとスピーカーが利用可能な環境
- インターネット接続（音声認識API使用時）

## インストール・実行方法

### 1. 依存関係のインストール
```bash
# 基本ライブラリのインストール
pip install -r requirements.txt

# ウェイクワード検知（Porcupine）を使用する場合
pip install pvporcupine

# ローカル音声認識（Whisper）を使用する場合  
pip install openai-whisper

# オプション：Google Text-to-Speech
pip install gTTS
```

### 2. システム要件の確認
```bash
# Python バージョン確認
python --version  # 3.8以上が必要

# Gemini CLI のインストール確認
gemini --version

# マイク・スピーカーのテスト
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### 3. 設定ファイルの編集
```bash
# 設定ファイルをコピー
cp config.example.json config.json

# 設定を編集
# config.json を編集
```

### 4. 実行
```bash
# システム起動
python main.py

# デバッグモードで実行
python main.py --debug
```

## ライセンス
（未定）

## 貢献
（未定）
