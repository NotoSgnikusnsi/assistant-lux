"""
音声出力モジュール
テキストを音声に変換して再生する機能を提供
キャッシュシステムによる高速化対応
"""

import pyttsx3
import threading
import logging
from typing import Optional, Dict, Any
import time
import os

try:
    import win32com.client
    WINDOWS_SPEECH_AVAILABLE = True
except ImportError:
    WINDOWS_SPEECH_AVAILABLE = False

from .audio_cache import AudioCache


class AudioOutputHandler:
    """音声出力を管理するクラス（キャッシュ対応）"""
    
    def __init__(self, 
                 rate: int = 200,
                 volume: float = 0.9,
                 voice_id: Optional[str] = None,
                 use_windows_speech: bool = True,
                 max_text_length: int = 300,
                 cache_phrases: Optional[list] = None):
        """
        初期化
        
        Args:
            rate: 音声の速度（words per minute）
            volume: 音量（0.0-1.0）
            voice_id: 使用する音声ID（Noneの場合はデフォルト）
            use_windows_speech: Windows Speech APIを優先使用するか
            max_text_length: 最大テキスト長
            cache_phrases: キャッシュするフレーズリスト
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.use_windows_speech = use_windows_speech and WINDOWS_SPEECH_AVAILABLE
        self.max_text_length = max_text_length
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 音声キャッシュシステム初期化
        if cache_phrases:
            voice_settings = {
                'rate': rate,
                'volume': volume,
                'voice_id': voice_id
            }
            self.audio_cache = AudioCache(cache_phrases, voice_settings)
            # バックグラウンドでキャッシュ生成開始
            self.cache_thread = self.audio_cache.pregenerate_cache()
        else:
            self.audio_cache = None
            self.cache_thread = None
        
        # 統計情報
        self.stats = {
            "total_outputs": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0
        }
        
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
        テキストを音声で読み上げ（キャッシュ対応）
        
        Args:
            text: 読み上げるテキスト
            blocking: 読み上げ完了まで待機するか
            
        Returns:
            成功したかどうか
        """
        if not text or not text.strip():
            print("⚠️  読み上げるテキストがありません")
            return False
        
        start_time = time.time()
        self.stats["total_outputs"] += 1
        
        try:
            # MCP STDERRなどのノイズを除去
            clean_text = self._clean_text(text)
            
            print(f"🔊 音声出力: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            
            if not clean_text.strip():
                print("⚠️  クリーン後のテキストが空です")
                return False
            
            # キャッシュから音声を取得試行
            if self.audio_cache:
                cached_audio = self.audio_cache.get_cached_audio(clean_text)
                if cached_audio:
                    self.stats["cache_hits"] += 1
                    print("⚡ キャッシュから音声再生")
                    # キャッシュされた音声を再生
                    cache_success = self._play_cached_audio(cached_audio, blocking)
                    if cache_success:
                        return True
                    else:
                        print("⚠️ キャッシュ再生失敗、通常の音声合成にフォールバック")
                        self.stats["cache_misses"] += 1
                else:
                    self.stats["cache_misses"] += 1
            else:
                # キャッシュが無効の場合
                self.stats["cache_misses"] += 1
            
            # キャッシュにない場合は通常の音声合成
            return self._synthesize_and_play(clean_text, blocking)
            
        except Exception as e:
            print(f"❌ 音声出力エラー: {e}")
            self.logger.error(f"Speech output error: {e}")
            return False
        finally:
            # 処理時間を記録
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
    
    def _play_cached_audio(self, audio_data: bytes, blocking: bool = True) -> bool:
        """
        キャッシュされた音声データを再生
        
        Args:
            audio_data: 音声データ
            blocking: 同期再生するか
            
        Returns:
            再生成功したかどうか
        """
        print("DEBUG: キャッシュ音声再生開始")
        
        # 最初にpygameでの再生を試行
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            
            # バイトデータから音声を再生
            import io
            audio_buffer = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_buffer)
            pygame.mixer.music.play()
            
            print("DEBUG: pygame音声再生開始")
            
            if blocking:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                print("DEBUG: pygame音声再生完了")
            
            return True
            
        except ImportError:
            print("DEBUG: pygameが利用できません、フォールバック再生を使用")
            # pygameが利用できない場合は一時ファイルで再生
            return self._play_cached_audio_fallback(audio_data, blocking)
        except Exception as e:
            print(f"⚠️ pygame音声再生エラー: {e}")
            print("DEBUG: フォールバック再生に切り替え")
            return self._play_cached_audio_fallback(audio_data, blocking)
    
    def _play_cached_audio_fallback(self, audio_data: bytes, blocking: bool = True) -> bool:
        """
        キャッシュ音声のフォールバック再生（一時ファイル使用）
        
        Args:
            audio_data: 音声データ
            blocking: 同期再生するか
            
        Returns:
            再生成功したかどうか
        """
        print("DEBUG: フォールバック音声再生開始")
        
        try:
            import tempfile
            import subprocess
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            print(f"DEBUG: 一時ファイル作成: {temp_file_path}")
            
            # Windowsの場合はシンプルなPowerShellコマンドで再生
            if os.name == 'nt':
                try:
                    if blocking:
                        # 同期再生 - SoundPlayerクラスを使用
                        cmd = f'$player = New-Object System.Media.SoundPlayer; $player.SoundLocation = "{temp_file_path}"; $player.PlaySync()'
                        result = subprocess.run(["powershell", "-Command", cmd], 
                                              capture_output=True, text=True, timeout=10)
                        print(f"DEBUG: PowerShell同期再生完了: {result.returncode}")
                        
                        # ファイル削除
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                        
                        return result.returncode == 0
                    else:
                        # 非同期再生
                        cmd = f'$player = New-Object System.Media.SoundPlayer; $player.SoundLocation = "{temp_file_path}"; $player.Play()'
                        subprocess.Popen(["powershell", "-Command", cmd])
                        print("DEBUG: PowerShell非同期再生開始")
                        
                        # 遅延削除
                        def delayed_cleanup():
                            time.sleep(5)
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass
                        threading.Thread(target=delayed_cleanup, daemon=True).start()
                        
                        return True
                        
                except Exception as e:
                    print(f"⚠️ PowerShell再生エラー: {e}")
                    # ファイルクリーンアップ
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                    return False
            else:
                # Windows以外の場合
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                return False
            
        except Exception as e:
            print(f"⚠️ フォールバック音声再生エラー: {e}")
            return False
    
    def _synthesize_and_play(self, clean_text: str, blocking: bool = True) -> bool:
        """
        音声合成して再生（従来の方法）
        
        Args:
            clean_text: クリーンアップされたテキスト
            blocking: 同期再生するか
            
        Returns:
            再生成功したかどうか
        """
        # Windows Speech APIを優先使用
        if self.use_windows_speech and self.win_speech:
            print("DEBUG: Windows Speech API使用")
            try:
                if blocking:
                    print("DEBUG: Windows Speech API同期再生開始")
                    self.win_speech.Speak(clean_text)
                    print("DEBUG: Windows Speech API同期再生完了")
                else:
                    print("DEBUG: Windows Speech API非同期再生開始")
                    self.win_speech.Speak(clean_text, 1)  # 非同期フラグ
                    print("DEBUG: Windows Speech API非同期再生完了")
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        音声出力の統計情報を取得
        
        Returns:
            統計情報辞書
        """
        total_outputs = self.stats["total_outputs"]
        cache_hits = self.stats["cache_hits"]
        cache_misses = self.stats["cache_misses"]
        
        stats = self.stats.copy()
        
        # 計算統計を追加
        if total_outputs > 0:
            stats["cache_hit_rate"] = cache_hits / total_outputs
            stats["average_processing_time"] = self.stats["total_processing_time"] / total_outputs
        else:
            stats["cache_hit_rate"] = 0.0
            stats["average_processing_time"] = 0.0
        
        # キャッシュシステムの統計も追加
        if self.audio_cache:
            cache_stats = self.audio_cache.get_cache_stats()
            stats.update(cache_stats)
        
        return stats
    
    def cleanup(self):
        """リソースの清理"""
        try:
            if self.engine:
                self.engine.stop()
            if self.audio_cache:
                self.audio_cache.clear_cache()
            print("🔒 音声出力システム終了")
        except Exception as e:
            self.logger.error(f"音声出力クリーンアップエラー: {e}")


def test_audio_output():
    """音声出力のテスト関数"""
    print("=== 音声出力テスト ===")
    audio_output = AudioOutputHandler(rate=200, volume=0.8)
    
    print("テキストを入力してください（quit/exit/終了で終了）:")
    
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
