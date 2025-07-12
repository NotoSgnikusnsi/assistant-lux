"""
常時音声監視モジュール
ストリーミング音声認識でウェイクワードを常時監視
音韻的類似度検証による精度向上機能付き
"""

import threading
import queue
import time
import datetime
import numpy as np
import pyaudio
import speech_recognition as sr
from typing import Optional, Callable, Tuple
import webrtcvad
import collections

# 音韻的類似度検証モジュールをインポート
try:
    from phonetic_similarity import EnhancedWakeWordVerifier
    PHONETIC_VERIFICATION_AVAILABLE = True
except ImportError:
    try:
        from src.phonetic_similarity import EnhancedWakeWordVerifier
        PHONETIC_VERIFICATION_AVAILABLE = True
    except ImportError:
        print("⚠️ 音韻的類似度検証モジュールが見つかりません。基本機能のみ使用します。")
        PHONETIC_VERIFICATION_AVAILABLE = False


class ContinuousSpeechMonitor:
    """常時音声監視クラス"""
    
    def __init__(self, language: str = "ja-JP", wake_words: list = None, audio_handler=None):
        """
        初期化
        
        Args:
            language: 認識言語
            wake_words: ウェイクワードリスト
            audio_handler: 音声出力ハンドラー（効果音再生用）
        """
        self.language = language
        self.wake_words = wake_words or ["ルクス", "るくす", "Lux", "lux"]
        self.audio_handler = audio_handler  # 音声出力ハンドラー
        
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
        
        # 音韻的検証器初期化
        if PHONETIC_VERIFICATION_AVAILABLE:
            self.phonetic_verifier = EnhancedWakeWordVerifier("ルクス")
            self.use_phonetic_verification = True
            print("✅ 音韻的類似度検証機能を有効化")
        else:
            self.phonetic_verifier = None
            self.use_phonetic_verification = False
            print("⚠️ 音韻的類似度検証機能は無効")
        
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
        self.is_processing = False  # 処理中フラグを追加
        self.audio_output_active = False  # 音声出力中フラグを追加
        self.monitoring_thread = None
        self.processing_thread = None
        
        # キューとコールバック
        self.audio_queue = queue.Queue()
        self.wake_word_callback = None
        self.command_callback = None
        
        # 統計情報
        self.detection_stats = {
            'total_detections': 0,
            'phonetic_verified': 0,
            'phonetic_rejected': 0,
            'basic_detections': 0
        }
        
        # 重複検知防止
        self.last_wake_word_text = ""
        self.last_wake_word_time = 0
        self.wake_word_cooldown = 3.0  # 秒単位のクールダウン時間
        self.audio_output_end_time = 0  # 音声出力終了時刻
        self.audio_output_suppression_time = 2.0  # 音声出力後の検知抑制時間
        
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
                
                # 音声出力中や処理中は音声検知を無視
                if self.audio_output_active or self.is_processing:
                    continue
                
                # 音声出力後の検知抑制時間チェック
                current_time = time.time()
                if current_time - self.audio_output_end_time < self.audio_output_suppression_time:
                    continue
                
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
        if not self.voice_buffer or self.is_processing:
            return
        
        # 処理開始フラグ設定
        self.is_processing = True
        
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
                    
                    # 効果音再生
                    if self.audio_handler:
                        success = self.audio_handler.play_wake_word_detected_sound()
                        if success:
                            print("🔊 ウェイクワード検知音を再生")
                        else:
                            print("⚠️ ウェイクワード検知音の再生に失敗")
                    else:
                        print("⚠️ audio_handlerが設定されていません")
                    
                    if self.wake_word_callback:
                        self.wake_word_callback(text, extracted_command)
                else:
                    print(f"📝 通常音声: '{text}'")
        
        except Exception as e:
            import traceback
            print(f"音声セグメント処理エラー: {e}")
            print(f"詳細エラー情報: {traceback.format_exc()}")
        finally:
            # 処理完了フラグリセット
            self.is_processing = False
    
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
        ウェイクワードチェック（音韻的検証強化版）
        
        Args:
            text: 認識されたテキスト
            
        Returns:
            (ウェイクワード検知フラグ, 抽出されたコマンド)
        """
        try:
            if not text:
                return False, ""
            
            # 重複検知防止チェック
            current_time = time.time()
            if (text == self.last_wake_word_text and 
                current_time - self.last_wake_word_time < self.wake_word_cooldown):
                print(f"🔄 重複ウェイクワードを無視: '{text}' (クールダウン: {self.wake_word_cooldown}秒)")
                return False, ""
            
            self.detection_stats['total_detections'] += 1
            
            # 基本的なウェイクワード検知
            basic_detected, command = self._basic_wake_word_check(text)
            
            if basic_detected:
                self.detection_stats['basic_detections'] += 1
                
                # 音韻的検証を実行
                if self.use_phonetic_verification and self.phonetic_verifier:
                    verification_result = self._phonetic_verification(text)
                    
                    if verification_result['is_verified']:
                        self.detection_stats['phonetic_verified'] += 1
                        print(f"✅ 音韻的検証成功: '{text}' (信頼度: {verification_result['confidence']:.2f})")
                        print(f"   処理時間: {verification_result['processing_time']:.1f}ms")
                        
                        # 成功時に重複防止記録を更新
                        self.last_wake_word_text = text
                        self.last_wake_word_time = current_time
                        
                        return True, command
                    else:
                        self.detection_stats['phonetic_rejected'] += 1
                        print(f"❌ 音韻的検証失敗: '{text}' (信頼度: {verification_result['confidence']:.2f})")
                        print(f"   誤検知を防止しました")
                        return False, ""
                else:
                    # 音韻的検証が無効の場合は基本検知結果を返す
                    # 成功時に重複防止記録を更新
                    self.last_wake_word_text = text
                    self.last_wake_word_time = current_time
                    return True, command
            
            return False, ""
            
        except Exception as e:
            import traceback
            print(f"ウェイクワードチェックエラー: {e}")
            print(f"詳細エラー情報: {traceback.format_exc()}")
            return False, ""
    
    def _basic_wake_word_check(self, text: str) -> Tuple[bool, str]:
        """
        基本的なウェイクワードチェック（従来ロジック）
        
        Args:
            text: 認識されたテキスト
            
        Returns:
            (ウェイクワード検知フラグ, 抽出されたコマンド)
        """
        text_lower = text.lower()
        
        # 特別処理：挨拶パターンでの誤認識対策
        greeting_corrections = {
            "おはようございます": "おはようルクス",
            "こんにちは": "ルクス",
            "こんばんは": "ルクス",
            "ありがとうございます": "ルクス"
        }
        
        # 挨拶誤認識の修正
        for incorrect, correct in greeting_corrections.items():
            if incorrect in text_lower:
                print(f"🔧 挨拶誤認識を修正: '{text}' → '{correct}' として処理")
                # コマンド抽出（修正後のテキストを使用）
                wake_word_index = correct.lower().find("ルクス".lower())
                if wake_word_index >= 0:
                    command = correct[wake_word_index + len("ルクス"):].strip()
                    command = command.lstrip('、。，,')
                    return True, command
                return True, ""
        
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
            "ルークス": "ルクス", "るーくす": "ルクス",  # 長音変化を追加
            "リクス": "ルクス", "りくす": "ルクス",      # 母音変化を追加
            "ラクス": "ルクス", "らくす": "ルクス",      # よくある誤認識
            # 特殊な誤認識パターン
            "ございます": "ルクス",   # 重要：敬語への誤変換対策
            "おはようございます": "おはようルクス",
            "こんにちは": "ルクス",   # 挨拶の誤認識対策
            "ありがとうございます": "ルクス",  # 敬語誤認識対策
            # 英語パターン拡張
            "luck": "Lux", "lacks": "Lux", "lux": "Lux"  
        }
        
        for fuzzy_word, wake_word in fuzzy_matches.items():
            if fuzzy_word.lower() in text_lower:
                fuzzy_index = text_lower.find(fuzzy_word.lower())
                command = text[fuzzy_index + len(fuzzy_word):].strip()
                command = command.lstrip('、。，,')
                return True, command
        
        return False, ""
    
    def _phonetic_verification(self, text: str) -> dict:
        """
        音韻的検証の実行
        
        Args:
            text: 検証対象テキスト
            
        Returns:
            検証結果辞書
        """
        # コンテキスト情報の構築
        context = {
            'text_length': len(text),
            'noise_level': self._estimate_noise_level(),
            'recognition_confidence': 0.9,  # Google Speech APIの場合は高めに設定
            'hour': datetime.datetime.now().hour
        }
        
        # 音韻的検証実行
        is_verified, confidence, details = self.phonetic_verifier.verify_wake_word(text, context)
        
        return {
            'is_verified': is_verified,
            'confidence': confidence,
            'processing_time': details.get('processing_time_ms', 0),
            'threshold_used': details.get('threshold_used', 0.7),
            'normalized_input': details.get('normalized_input', ''),
            'performance_warning': details.get('performance_warning', False)
        }
    
    def _estimate_noise_level(self) -> float:
        """
        ノイズレベルの推定（簡易版）
        
        Returns:
            推定ノイズレベル (0.0-1.0)
        """
        # 実際の実装では音声バッファの分析等を行う
        # ここでは簡易的な値を返す
        if len(self.audio_buffer) > 10:
            # 音声バッファの音量変動からノイズレベルを推定
            volumes = []
            for audio_chunk in list(self.audio_buffer)[-10:]:
                if isinstance(audio_chunk, np.ndarray):
                    volume = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
                    volumes.append(volume)
            
            if volumes:
                # 音量の標準偏差が大きいほどノイズが多いと推定
                std_volume = np.std(volumes)
                return min(1.0, std_volume / 1000.0)
        
        return 0.3  # デフォルト値
    
    def get_detection_statistics(self) -> dict:
        """
        検知統計情報の取得
        
        Returns:
            統計情報辞書
        """
        stats = self.detection_stats.copy()
        
        if self.use_phonetic_verification and self.phonetic_verifier:
            phonetic_stats = self.phonetic_verifier.get_verification_statistics()
            stats.update({
                'phonetic_accuracy_rate': phonetic_stats.get('accuracy_rate', 0.0),
                'phonetic_false_positive_prevention_rate': phonetic_stats.get('false_positive_prevention_rate', 0.0),
                'average_phonetic_processing_time': phonetic_stats.get('average_processing_time', 0.0)
            })
        
        return stats
    
    def set_audio_output_active(self, active: bool):
        """
        音声出力状態を設定
        
        Args:
            active: 音声出力中かどうか
        """
        self.audio_output_active = active
        if active:
            # 音声出力中は音声バッファをクリア
            self.voice_buffer = []
            self.is_voice_active = False
            self.silence_duration = 0
            print("🔇 音声出力中のため音声検知を一時停止")
        else:
            # 音声出力終了時刻を記録
            self.audio_output_end_time = time.time()
            print(f"🎤 音声検知を再開 (抑制時間: {self.audio_output_suppression_time}秒)")
    
    def enable_phonetic_verification(self, enable: bool = True):
        """
        音韻的検証の有効/無効切り替え
        
        Args:
            enable: 有効にするかどうか
        """
        if PHONETIC_VERIFICATION_AVAILABLE and self.phonetic_verifier:
            self.use_phonetic_verification = enable
            status = "有効" if enable else "無効"
            print(f"音韻的検証機能を{status}にしました")
        else:
            print("音韻的検証機能は利用できません")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        self.stop_monitoring()
        
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()
        
        # 統計情報表示
        if self.use_phonetic_verification:
            print("\n=== 音韻的検証統計 ===")
            stats = self.get_detection_statistics()
            print(f"総検知回数: {stats['total_detections']}")
            print(f"基本検知成功: {stats['basic_detections']}")
            print(f"音韻的検証成功: {stats['phonetic_verified']}")
            print(f"音韻的検証却下: {stats['phonetic_rejected']}")
            if 'phonetic_accuracy_rate' in stats:
                print(f"音韻的検証精度: {stats['phonetic_accuracy_rate']:.1%}")
                print(f"誤検知防止率: {stats['phonetic_false_positive_prevention_rate']:.1%}")
                print(f"平均処理時間: {stats['average_phonetic_processing_time']:.2f}ms")


def test_continuous_speech():
    """常時音声監視のテスト（音韻的検証対応版）"""
    print("=== 常時音声監視テスト（音韻的検証付き） ===")
    
    def on_wake_word(text, command):
        print(f"✅ ウェイクワード検知: '{text}', コマンド: '{command}'")
    
    monitor = ContinuousSpeechMonitor()
    monitor.set_wake_word_callback(on_wake_word)
    
    # 音韻的検証の状態表示
    if monitor.use_phonetic_verification:
        print("🔍 音韻的類似度検証機能: 有効")
    else:
        print("⚠️ 音韻的類似度検証機能: 無効")
    
    try:
        monitor.start_monitoring()
        print("監視中... 's'キーで統計表示, 'p'キーで音韻的検証切り替え, Ctrl+Cで終了")
        
        import sys
        import select
        
        while True:
            # キー入力チェック（Windows対応）
            try:
                if sys.platform == "win32":
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 's':
                            # 統計表示
                            stats = monitor.get_detection_statistics()
                            print(f"\n--- 検知統計 ---")
                            print(f"総検知: {stats['total_detections']}, "
                                  f"基本検知: {stats['basic_detections']}, "
                                  f"音韻検証成功: {stats['phonetic_verified']}, "
                                  f"音韻検証却下: {stats['phonetic_rejected']}")
                        elif key == 'p':
                            # 音韻的検証切り替え
                            monitor.enable_phonetic_verification(not monitor.use_phonetic_verification)
                else:
                    # Linux/Mac用（簡易版）
                    pass
            except:
                pass
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n監視終了")
    finally:
        monitor.cleanup()


def test_phonetic_verification_only():
    """音韻的検証機能のみのテスト"""
    print("=== 音韻的検証機能単体テスト ===")
    
    if not PHONETIC_VERIFICATION_AVAILABLE:
        print("❌ 音韻的検証機能が利用できません")
        return
    
    # phonetic_similarity.pyのテスト関数を呼び出し
    from phonetic_similarity import test_phonetic_verification
    test_phonetic_verification()


if __name__ == "__main__":
    # テストメニュー
    print("音韻的類似度検証システム テストメニュー")
    print("1. 音韻的検証機能単体テスト")
    print("2. 常時音声監視テスト（音韻的検証付き）")
    
    try:
        choice = input("選択してください (1 or 2): ").strip()
        if choice == "1":
            test_phonetic_verification_only()
        elif choice == "2":
            test_continuous_speech()
        else:
            print("常時音声監視テストを実行します")
            test_continuous_speech()
    except KeyboardInterrupt:
        print("\nテストを終了します")
