"""
音声アシスタント メインアプリケーション
ウェイクワード検知と音声入力機能
"""

import time
import signal
import sys
from src.audio_input import AudioInputHandler
from src.speech_recognition import SpeechRecognizer
from src.gemini_client import GeminiClient


class VoiceAssistant:
    """音声アシスタントのメインクラス"""
    
    def __init__(self):
        """初期化"""
        print("=== 音声アシスタント起動中 ===")
        
        # コンポーネント初期化
        self.audio_handler = AudioInputHandler(recording_duration=5)
        self.speech_recognizer = SpeechRecognizer(language="ja-JP")
        self.gemini_client = GeminiClient(debug=False)
        
        # 状態管理
        self.is_running = True
        self.wake_words = [
            # メインウェイクワード - アシスタント名「ルクス」
            "ルクス", "るくす", "Lux", "lux", "LUX"
        ]
        
        print("初期化完了！")
    
    def listen_for_wake_word(self) -> tuple[bool, str]:
        """
        ウェイクワードを監視
        
        Returns:
            (ウェイクワードが検知されたか, 一緒に話されたコマンド)
        """
        print("\n--- ウェイクワード待機中 ---")
        print(f"ウェイクワード: {', '.join(self.wake_words)}")
        print("何か話してください...")
        
        try:
            # マイクから音声認識
            text = self.speech_recognizer.recognize_from_microphone(
                timeout=30,  # 30秒でタイムアウト
                phrase_timeout=5  # 5秒で区切り
            )
            
            if text:
                print(f"音声入力: '{text}'")
                
                # ウェイクワード検知とコマンド抽出
                is_wake_word, extracted_command = self.speech_recognizer.extract_command_from_wake_word_text(
                    text, self.wake_words
                )
                
                if is_wake_word:
                    print("🎤 ウェイクワード検知！アシスタントを起動します")
                    if extracted_command:
                        print(f"同時に検知されたコマンド: '{extracted_command}'")
                    return True, extracted_command
                else:
                    print("ウェイクワードではありません。待機を続けます...")
                    return False, ""
            else:
                return False, ""
                
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"ウェイクワード監視エラー: {e}")
            return False, ""
    
    def listen_for_command(self, initial_command: str = "") -> str:
        """
        コマンド入力を待機
        
        Args:
            initial_command: ウェイクワードと同時に認識されたコマンド
            
        Returns:
            認識されたコマンドテキスト
        """
        # 既にコマンドが抽出されている場合
        if initial_command.strip():
            print(f"\n--- コマンド処理 ---")
            print(f"ウェイクワードと同時に認識されたコマンド: '{initial_command}'")
            return initial_command.strip()
        
        print("\n--- コマンド入力待機 ---")
        print("ご用件をお話しください（10秒以内）...")
        
        try:
            # 音声データを録音
            audio_data = self.audio_handler.record_audio(duration=10)
            
            if len(audio_data) > 0:
                # 音声認識
                text = self.speech_recognizer.recognize_from_audio_data(
                    audio_data, 
                    self.audio_handler.sample_rate
                )
                
                if text:
                    print(f"📝 認識されたコマンド: '{text}'")
                    return text
                else:
                    print("音声を認識できませんでした")
                    return ""
            else:
                print("音声データがありません")
                return ""
                
        except Exception as e:
            print(f"コマンド入力エラー: {e}")
            return ""
    
    def process_command(self, command: str):
        """
        コマンドを処理し、Gemini CLIに送信して応答を取得
        
        Args:
            command: 認識されたコマンド
        """
        print(f"\n=== コマンド処理 ===")
        print(f"📝 入力内容: {command}")
        
        # 終了コマンドのチェック
        if any(word in command.lower() for word in ["終了", "しゅうりょう", "バイバイ", "ばいばい", "exit", "quit"]):
            print("👋 音声アシスタントを終了します")
            self.is_running = False
            return
        
        # Gemini CLIに送信
        print("🤖 Geminiに問い合わせ中...")
        try:
            response = self.gemini_client.send_command(command)
            
            if response:
                print(f"\n💬 【Gemini応答】")
                print(f"{response}")
                print(f"{'='*50}")
            else:
                print("❌ Geminiからの応答を取得できませんでした")
                
        except Exception as e:
            print(f"❌ Gemini通信エラー: {e}")
            print("接続状況を確認してください")
    
    def run(self):
        """メインループ実行"""
        print("\n🎤 音声アシスタントが開始されました")
        print("Ctrl+C で終了できます")
        
        try:
            while self.is_running:
                # 1. ウェイクワード待機（コマンドも同時抽出）
                wake_word_detected, extracted_command = self.listen_for_wake_word()
                
                if wake_word_detected:
                    # 2. コマンド入力待機（既に抽出されている場合はそれを使用）
                    command = self.listen_for_command(extracted_command)
                    
                    if command:
                        # 3. コマンド処理
                        self.process_command(command)
                    
                    print("\n" + "="*50)
                
                # 少し待機
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n👋 音声アシスタントを終了します")
        except Exception as e:
            print(f"\n予期せぬエラー: {e}")
        finally:
            print("アプリケーションを終了しました")


def signal_handler(signum, frame):
    """シグナルハンドラー（Ctrl+C対応）"""
    print("\n\n終了シグナルを受信しました...")
    sys.exit(0)


def main():
    """メイン関数"""
    # シグナルハンドラー設定
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 音声アシスタント起動
        assistant = VoiceAssistant()
        assistant.run()
        
    except Exception as e:
        print(f"起動エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
