"""
並列音声認識システム
音声認識処理をバックグラウンドで実行し、レスポンス性を向上させる
"""

import asyncio
import threading
import queue
import speech_recognition as sr
import logging
from typing import Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import time


class ParallelSpeechRecognizer:
    """並列音声認識を管理するクラス"""
    
    def __init__(self, language: str = "ja-JP", max_workers: int = 2):
        """
        初期化
        
        Args:
            language: 認識言語
            max_workers: 並列処理の最大ワーカー数
        """
        self.language = language
        self.max_workers = max_workers
        
        # 音声認識エンジン
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # 並列処理用
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.recognition_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # 状態管理
        self.is_running = False
        self.current_futures: list[Future] = []
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 統計情報
        self.stats = {
            "total_recognitions": 0,
            "successful_recognitions": 0,
            "parallel_recognitions": 0,
            "average_processing_time": 0.0
        }
        
        print("🎙️ 並列音声認識システム初期化完了")
        
        # マイクの調整
        self._calibrate_microphone()
    
    def _calibrate_microphone(self):
        """マイクの環境ノイズ調整"""
        try:
            print("🔧 マイク環境調整中...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ マイク調整完了")
        except Exception as e:
            self.logger.warning(f"マイク調整エラー: {e}")
    
    def recognize_speech_async(self, audio_data: sr.AudioData) -> Future[Optional[str]]:
        """
        音声認識を非同期で実行
        
        Args:
            audio_data: 音声データ
            
        Returns:
            音声認識結果のFuture
        """
        def recognize_worker():
            start_time = time.time()
            try:
                self.stats["total_recognitions"] += 1
                
                # Google Speech Recognition使用
                text = self.recognizer.recognize_google(
                    audio_data, 
                    language=self.language,
                    show_all=False
                )
                
                processing_time = time.time() - start_time
                self._update_processing_time_stats(processing_time)
                
                self.stats["successful_recognitions"] += 1
                print(f"🎯 音声認識成功: '{text}' ({processing_time:.2f}秒)")
                return text
                
            except sr.UnknownValueError:
                print("⚠️ 音声を認識できませんでした")
                return None
            except sr.RequestError as e:
                self.logger.error(f"音声認識サービスエラー: {e}")
                return None
            except Exception as e:
                self.logger.error(f"音声認識エラー: {e}")
                return None
        
        # 並列実行
        future = self.executor.submit(recognize_worker)
        self.current_futures.append(future)
        self.stats["parallel_recognitions"] += 1
        
        return future
    
    def recognize_speech_blocking(self, audio_data: sr.AudioData, timeout: float = 10.0) -> Optional[str]:
        """
        音声認識をブロッキング実行（従来互換）
        
        Args:
            audio_data: 音声データ
            timeout: タイムアウト時間
            
        Returns:
            認識されたテキスト
        """
        future = self.recognize_speech_async(audio_data)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            self.logger.error(f"音声認識タイムアウト: {e}")
            return None
    
    def start_continuous_recognition(self, 
                                   callback: Callable[[str], None],
                                   wake_word_callback: Optional[Callable[[str], bool]] = None):
        """
        連続音声認識を開始
        
        Args:
            callback: 認識結果のコールバック関数
            wake_word_callback: ウェイクワード検出のコールバック関数
        """
        self.is_running = True
        
        def continuous_worker():
            print("🔄 連続音声認識開始")
            
            while self.is_running:
                try:
                    # 音声録音
                    with self.microphone as source:
                        print("🎤 音声待機中...")
                        # 短いタイムアウトで非ブロッキング録音
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    # 非同期で音声認識開始
                    future = self.recognize_speech_async(audio)
                    
                    # ノンブロッキングで結果確認
                    def check_result():
                        try:
                            result = future.result(timeout=0.1)  # 短いタイムアウト
                            if result:
                                # ウェイクワードチェック
                                if wake_word_callback and wake_word_callback(result):
                                    callback(result)
                                elif not wake_word_callback:
                                    callback(result)
                        except:
                            pass  # まだ完了していない
                    
                    # 結果チェックを別スレッドで実行
                    threading.Thread(target=check_result, daemon=True).start()
                    
                except sr.WaitTimeoutError:
                    continue  # タイムアウトは正常
                except Exception as e:
                    self.logger.error(f"連続認識エラー: {e}")
                    time.sleep(0.1)
        
        # バックグラウンドで開始
        thread = threading.Thread(target=continuous_worker, daemon=True)
        thread.start()
        return thread
    
    def stop_continuous_recognition(self):
        """連続音声認識を停止"""
        self.is_running = False
        print("⏹️ 連続音声認識停止")
    
    def _update_processing_time_stats(self, processing_time: float):
        """処理時間統計を更新"""
        current_avg = self.stats["average_processing_time"]
        total = self.stats["successful_recognitions"]
        
        if total == 1:
            self.stats["average_processing_time"] = processing_time
        else:
            # 移動平均で更新
            self.stats["average_processing_time"] = (current_avg * (total - 1) + processing_time) / total
    
    def cleanup_completed_futures(self):
        """完了したFutureをクリーンアップ"""
        self.current_futures = [f for f in self.current_futures if not f.done()]
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        self.cleanup_completed_futures()
        
        success_rate = 0
        if self.stats["total_recognitions"] > 0:
            success_rate = self.stats["successful_recognitions"] / self.stats["total_recognitions"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "active_futures": len(self.current_futures),
            "is_running": self.is_running
        }
    
    def shutdown(self):
        """システム終了"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        print("🔒 並列音声認識システム終了")
