"""
常時音声監視モジュール
ストリーミング音声認識でウェイクワードを常時監視
"""

import threading
import queue
import time
import numpy as np
import pyaudio
import speech_recognition as sr
from typing import Optional, Callable, Tuple
import webrtcvad
import collections


class ContinuousSpeechMonitor:
    """常時音声監視クラス"""
    
    def __init__(self, language: str = "ja-JP", wake_words: list = None):
        """
        初期化
        
        Args:
            language: 認識言語
            wake_words: ウェイクワードリスト
        """
        self.language = language
        self.wake_words = wake_words or ["ルクス", "るくす", "Lux", "lux"]
        
        # 音声設定
        self.sample_rate = 16000
        self.chunk_duration_ms = 30  # 30ms chunks
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
        self.format = pyaudio.paInt16
        self.channels = 1
        
        # PyAudio初期化
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # 音声認識初期化
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8
        
        # VAD (Voice Activity Detection) 初期化
        self.vad = webrtcvad.Vad(2)  # 感度: 0(低) - 3(高)
        self.volume_threshold = 500  # フォールバック用音量閾値
        
        # バッファ管理
        self.audio_buffer = collections.deque(maxlen=100)  # 約3秒分
        self.voice_buffer = []
        self.is_voice_active = False
        self.voice_start_time = None
        self.silence_duration = 0
        
        # 制御フラグ
        self.is_running = False
        self.monitoring_thread = None
        self.processing_thread = None
        
        # キューとコールバック
        self.audio_queue = queue.Queue()
        self.wake_word_callback = None
        self.command_callback = None
        
        print("常時音声監視システム初期化完了")
    
    def set_wake_word_callback(self, callback: Callable[[str, str], None]):
        """
        ウェイクワード検知時のコールバック設定
        
        Args:
            callback: (検知テキスト, 抽出コマンド) -> None
        """
        self.wake_word_callback = callback
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """
        コマンド検知時のコールバック設定
        
        Args:
            callback: (コマンドテキスト) -> None
        """
        self.command_callback = callback
    
    def start_monitoring(self):
        """音声監視開始"""
        if self.is_running:
            return
        
        print("常時音声監視を開始します...")
        
        try:
            # 音声ストリーム開始
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_running = True
            
            # 監視スレッド開始
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
            
            self.monitoring_thread.start()
            self.processing_thread.start()
            
            print("✅ 常時音声監視開始")
            
        except Exception as e:
            print(f"音声監視開始エラー: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """音声監視停止"""
        if not self.is_running:
            return
        
        print("常時音声監視を停止します...")
        
        self.is_running = False
        
        # ストリーム停止
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # スレッド終了待機
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        
        print("✅ 常時音声監視停止")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio コールバック - 音声データの受信
        """
        try:
            self.audio_queue.put(in_data)
        except:
            pass
        return (None, pyaudio.paContinue)
    
    def _monitor_loop(self):
        """音声監視メインループ"""
        while self.is_running:
            try:
                # 音声データ取得（タイムアウト付き）
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # 音声データをNumPy配列に変換
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                self.audio_buffer.append(audio_np)
                
                # VADで音声活動検知
                is_speech = self._detect_voice_activity(audio_data)
                
                if is_speech:
                    if not self.is_voice_active:
                        # 音声開始
                        self.is_voice_active = True
                        self.voice_start_time = time.time()
                        self.voice_buffer = list(self.audio_buffer)  # 過去のバッファも含める
                        print("🎤 音声検知")
                    else:
                        # 音声継続
                        self.voice_buffer.append(audio_np)
                    
                    self.silence_duration = 0
                else:
                    if self.is_voice_active:
                        self.silence_duration += self.chunk_duration_ms
                        self.voice_buffer.append(audio_np)
                        
                        # 音声終了判定（500ms以上の無音）
                        if self.silence_duration >= 500:
                            self._process_voice_segment()
                            self.is_voice_active = False
                            self.voice_buffer = []
                            self.silence_duration = 0
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"音声監視エラー: {e}")
    
    def _process_loop(self):
        """音声処理ループ（別スレッド）"""
        # このスレッドは将来的にバックグラウンド処理用
        while self.is_running:
            time.sleep(0.1)
    
    def _detect_voice_activity(self, audio_data: bytes) -> bool:
        """
        VADを使用した音声活動検知
        
        Args:
            audio_data: 音声データ
            
        Returns:
            音声が検知されたかどうか
        """
        try:
            # VADは10ms, 20ms, 30msのチャンクサイズをサポート
            return self.vad.is_speech(audio_data, self.sample_rate)
        except:
            # VADエラー時は音量で判定
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            volume = np.sqrt(np.mean(audio_np**2))
            return volume > self.volume_threshold
    
    def _process_voice_segment(self):
        """音声セグメントの処理"""
        if not self.voice_buffer:
            return
        
        try:
            # 音声バッファを結合
            audio_segment = np.concatenate(self.voice_buffer)
            
            # 音声認識実行
            text = self._recognize_audio_segment(audio_segment)
            
            if text:
                print(f"🎯 音声認識: '{text}'")
                
                # ウェイクワード検知
                is_wake_word, extracted_command = self._check_wake_word(text)
                
                if is_wake_word:
                    print(f"🚨 ウェイクワード検知: '{text}'")
                    if self.wake_word_callback:
                        self.wake_word_callback(text, extracted_command)
                else:
                    print(f"📝 通常音声: '{text}'")
        
        except Exception as e:
            print(f"音声セグメント処理エラー: {e}")
    
    def _recognize_audio_segment(self, audio_data: np.ndarray) -> Optional[str]:
        """
        音声セグメントを認識
        
        Args:
            audio_data: 音声データ
            
        Returns:
            認識されたテキスト
        """
        try:
            # 音声データを正規化
            audio_data = audio_data.astype(np.float32) / 32768.0
            
            # speech_recognition用のAudioDataオブジェクト作成
            audio_bytes = (audio_data * 32768).astype(np.int16).tobytes()
            audio_sr = sr.AudioData(audio_bytes, self.sample_rate, 2)
            
            # Google Speech Recognition実行
            text = self.recognizer.recognize_google(audio_sr, language=self.language)
            return text
            
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"音声認識サービスエラー: {e}")
            return None
        except Exception as e:
            print(f"音声認識エラー: {e}")
            return None
    
    def _check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        ウェイクワードチェック
        
        Args:
            text: 認識されたテキスト
            
        Returns:
            (ウェイクワード検知フラグ, 抽出されたコマンド)
        """
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        # ウェイクワード検知
        for wake_word in self.wake_words:
            wake_word_lower = wake_word.lower()
            if wake_word_lower in text_lower:
                # コマンド抽出
                wake_word_index = text_lower.find(wake_word_lower)
                command = text[wake_word_index + len(wake_word):].strip()
                command = command.lstrip('、。，,')
                return True, command
        
        # 曖昧一致チェック
        fuzzy_matches = {
            "ラックス": "ルクス", "らっくす": "ルクス",  
            "ルックス": "ルクス", "るっくす": "ルクス",
            "luck": "Lux", "lacks": "Lux"
        }
        
        for fuzzy_word, wake_word in fuzzy_matches.items():
            if fuzzy_word.lower() in text_lower:
                fuzzy_index = text_lower.find(fuzzy_word.lower())
                command = text[fuzzy_index + len(fuzzy_word):].strip()
                command = command.lstrip('、。，,')
                return True, command
        
        return False, ""
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.stop_monitoring()
        
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()


def test_continuous_speech():
    """常時音声監視のテスト"""
    print("=== 常時音声監視テスト ===")
    
    def on_wake_word(text, command):
        print(f"✅ ウェイクワード検知: '{text}', コマンド: '{command}'")
    
    monitor = ContinuousSpeechMonitor()
    monitor.set_wake_word_callback(on_wake_word)
    
    try:
        monitor.start_monitoring()
        print("監視中... Ctrl+Cで終了")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n監視終了")
    finally:
        monitor.cleanup()


if __name__ == "__main__":
    test_continuous_speech()
