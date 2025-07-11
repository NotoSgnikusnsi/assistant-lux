"""
音声出力モジュール
テキストを音声に変換して再生する機能を提供
"""

import pyttsx3
import threading
import logging
from typing import Optional, Dict, Any

try:
    import win32com.client
    WINDOWS_SPEECH_AVAILABLE = True
except ImportError:
    WINDOWS_SPEECH_AVAILABLE = False


class AudioOutputHandler:
    """音声出力を管理するクラス"""
    
    def __init__(self, 
                 rate: int = 200,
                 volume: float = 0.9,
                 voice_id: Optional[str] = None,
                 use_windows_speech: bool = True):
        """
        初期化
        
        Args:
            rate: 音声の速度（words per minute）
            volume: 音量（0.0-1.0）
            voice_id: 使用する音声ID（Noneの場合はデフォルト）
            use_windows_speech: Windows Speech APIを優先使用するか
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.use_windows_speech = use_windows_speech and WINDOWS_SPEECH_AVAILABLE
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # Windows Speech API初期化
        if self.use_windows_speech:
            try:
                self.win_speech = win32com.client.Dispatch("SAPI.SpVoice")
                print(f"Windows Speech API初期化完了")
            except Exception as e:
                print(f"⚠️ Windows Speech API初期化失敗: {e}")
                self.use_windows_speech = False
                self.win_speech = None
        else:
            self.win_speech = None
        
        # TTS エンジン初期化（フォールバック用）
        try:
            self.engine = pyttsx3.init()
            self._configure_engine()
            print(f"音声出力初期化完了: 速度={rate}, 音量={volume}")
        except Exception as e:
            print(f"⚠️  音声出力初期化エラー: {e}")
            self.engine = None
    
    def _configure_engine(self):
        """TTSエンジンの設定"""
        if not self.engine:
            return
            
        try:
            # エンジンを一度停止してリセット
            self.engine.stop()
            
            # 音声速度設定
            self.engine.setProperty('rate', self.rate)
            
            # 音量設定（最大値に設定）
            self.engine.setProperty('volume', 1.0)  # 常に最大音量
            
            # 音声の選択
            voices = self.engine.getProperty('voices')
            if voices:
                if self.voice_id:
                    # 指定された音声IDを使用
                    for voice in voices:
                        if self.voice_id in voice.id:
                            self.engine.setProperty('voice', voice.id)
                            print(f"音声設定: {voice.name}")
                            break
                else:
                    # 日本語音声を優先的に選択
                    japanese_voice = None
                    for voice in voices:
                        if voice.languages and any('ja' in lang.lower() for lang in voice.languages):
                            japanese_voice = voice
                            break
                        # 代替として女性音声を選択
                        elif 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                            japanese_voice = voice
                    
                    if japanese_voice:
                        self.engine.setProperty('voice', japanese_voice.id)
                        print(f"音声設定: {japanese_voice.name}")
                    else:
                        print("デフォルト音声を使用")
            
            # エンジンを再初期化
            import time
            time.sleep(0.1)  # 短い待機
            
        except Exception as e:
            print(f"⚠️  音声エンジン設定エラー: {e}")
    
    def get_available_voices(self) -> list:
        """利用可能な音声一覧を取得"""
        if not self.engine:
            return []
            
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            print("\n=== 利用可能な音声 ===")
            for i, voice in enumerate(voices):
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages if voice.languages else ['不明']
                }
                voice_list.append(voice_info)
                print(f"{i}: {voice.name} ({', '.join(voice_info['languages'])})")
            
            return voice_list
        except Exception as e:
            print(f"音声一覧取得エラー: {e}")
            return []
    
    def speak_text(self, text: str, blocking: bool = True) -> bool:
        """
        テキストを音声で読み上げ
        
        Args:
            text: 読み上げるテキスト
            blocking: 読み上げ完了まで待機するか
            
        Returns:
            成功したかどうか
        """
        if not text or not text.strip():
            print("⚠️  読み上げるテキストがありません")
            return False
        
        try:
            # MCP STDERRなどのノイズを除去
            clean_text = self._clean_text(text)
            
            print(f"🔊 音声出力: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            print(f"DEBUG: クリーン前の長さ: {len(text)}, クリーン後の長さ: {len(clean_text)}")
            
            if not clean_text.strip():
                print("⚠️  クリーン後のテキストが空です")
                return False
            
            # Windows Speech APIを優先使用
            if self.use_windows_speech and self.win_speech:
                print("DEBUG: Windows Speech API使用")
                try:
                    if blocking:
                        self.win_speech.Speak(clean_text)
                    else:
                        self.win_speech.Speak(clean_text, 1)  # 非同期フラグ
                    print("DEBUG: Windows Speech API再生完了")
                    return True
                except Exception as e:
                    print(f"⚠️ Windows Speech APIエラー: {e}")
                    # フォールバックでpyttsx3を使用
            
            # pyttsx3エンジンを使用
            if not self.engine:
                print("❌ 音声エンジンが利用できません")
                return False
            
            if blocking:
                # 同期実行（読み上げ完了まで待機）
                print("DEBUG: pyttsx3同期音声再生開始")
                
                # エンジンをリセットして音量を確実に設定
                self.engine.stop()
                self.engine.setProperty('volume', 1.0)
                
                # テキストを設定して実行
                self.engine.say(clean_text)
                self.engine.runAndWait()
                print("DEBUG: pyttsx3同期音声再生完了")
            else:
                # 非同期実行（バックグラウンドで読み上げ）
                print("DEBUG: pyttsx3非同期音声再生開始")
                def speak_async():
                    self.engine.stop()
                    self.engine.setProperty('volume', 1.0)
                    self.engine.say(clean_text)
                    self.engine.runAndWait()
                    print("DEBUG: pyttsx3非同期音声再生完了")
                
                thread = threading.Thread(target=speak_async)
                thread.daemon = True
                thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ 音声出力エラー: {e}")
            self.logger.error(f"Speech output error: {e}")
            return False
    
    def _clean_text(self, text: str) -> str:
        """
        テキストをクリーンアップ（読み上げに不適切な部分を除去）
        
        Args:
            text: 元のテキスト
            
        Returns:
            クリーンアップされたテキスト
        """
        import re
        
        # MCP STDERRやデバッグ情報を除去
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 除外するパターン（より包括的に）
            skip_patterns = [
                r'^MCP STDERR',
                r'^\[DEBUG\]',
                r'^\[I \d{4}-\d{2}-\d{2}',
                r'^Flushing log events',
                r'HTTP Request:',
                r'Processing request of type',
                r'HTTP/1\.1 \d+',
                r'httpx\]',
                r'mcp\.server\.lowlevel\.server\]',
                r'Home Assistant\):',
                r'^\s*$'  # 空行
            ]
            
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line):
                    should_skip = True
                    break
            
            if not should_skip and line:
                clean_lines.append(line)
        
        clean_text = ' '.join(clean_lines)
        
        # さらにノイズ除去（単語レベル）
        clean_text = re.sub(r'MCP STDERR.*?:', '', clean_text)
        clean_text = re.sub(r'\[I \d{4}-\d{2}-\d{2}.*?\]', '', clean_text)
        clean_text = re.sub(r'HTTP Request:.*?"', '', clean_text)
        
        # 複数のスペースを1つにまとめる
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # 長すぎる場合は最初の部分のみ使用
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        return clean_text
    
    def stop_speaking(self):
        """読み上げを停止"""
        if self.engine:
            try:
                self.engine.stop()
                print("🔇 音声出力を停止しました")
            except Exception as e:
                print(f"音声停止エラー: {e}")
    
    def set_rate(self, rate: int):
        """音声速度を変更"""
        self.rate = rate
        if self.engine:
            try:
                self.engine.setProperty('rate', rate)
                print(f"音声速度を {rate} WPM に変更しました")
            except Exception as e:
                print(f"音声速度変更エラー: {e}")
    
    def set_volume(self, volume: float):
        """音量を変更"""
        self.volume = max(0.0, min(1.0, volume))  # 0.0-1.0の範囲に制限
        if self.engine:
            try:
                self.engine.setProperty('volume', self.volume)
                print(f"音量を {self.volume} に変更しました")
            except Exception as e:
                print(f"音量変更エラー: {e}")
    
    def test_speech(self, test_text: str = "こんにちは。音声テストです。"):
        """音声出力のテスト"""
        print("\n=== 音声出力テスト ===")
        print(f"テストテキスト: {test_text}")
        
        success = self.speak_text(test_text, blocking=True)
        
        if success:
            print("✅ 音声出力テスト成功")
        else:
            print("❌ 音声出力テスト失敗")
        
        return success


def test_audio_output():
    """音声出力のテスト関数"""
    print("=== 音声出力テスト ===")
    
    # 音声出力ハンドラー初期化
    audio_output = AudioOutputHandler()
    
    # 利用可能音声の表示
    audio_output.get_available_voices()
    
    # 基本テスト
    audio_output.test_speech()
    
    # インタラクティブテスト
    print("\n--- インタラクティブテスト ---")
    print("読み上げるテキストを入力してください（'quit'で終了）:")
    
    try:
        while True:
            user_input = input("\n> ")
            if user_input.lower() in ['quit', 'exit', '終了']:
                break
            
            if user_input.strip():
                audio_output.speak_text(user_input, blocking=True)
            
    except KeyboardInterrupt:
        print("\nテストを終了します")
    
    audio_output.stop_speaking()


if __name__ == "__main__":
    test_audio_output()
