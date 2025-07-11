"""
動的音声品質調整システム
用途に応じて音声のサンプルレートを動的に変更して処理速度を最適化
"""

import pyaudio
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple
import threading
import time


class DynamicAudioOptimizer:
    """動的音声品質調整を管理するクラス"""
    
    def __init__(self, quality_profiles: Dict[str, Dict[str, Any]]):
        """
        初期化
        
        Args:
            quality_profiles: 品質プロファイル設定
        """
        self.quality_profiles = quality_profiles
        self.current_profile = "conversation"  # デフォルト
        self.audio_interface = pyaudio.PyAudio()
        
        # 現在の設定
        self.current_settings = self.quality_profiles[self.current_profile].copy()
        
        # 統計情報
        self.stats = {
            "profile_switches": 0,
            "processing_time_by_profile": {},
            "current_profile": self.current_profile
        }
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        print("🎛️ 動的音声品質調整システム初期化完了")
        print(f"📊 利用可能プロファイル: {list(self.quality_profiles.keys())}")
    
    def switch_profile(self, profile_name: str) -> bool:
        """
        音声品質プロファイルを切り替え
        
        Args:
            profile_name: プロファイル名
            
        Returns:
            切り替え成功時True
        """
        if profile_name not in self.quality_profiles:
            self.logger.warning(f"存在しないプロファイル: {profile_name}")
            return False
        
        if profile_name != self.current_profile:
            old_profile = self.current_profile
            self.current_profile = profile_name
            self.current_settings = self.quality_profiles[profile_name].copy()
            self.stats["profile_switches"] += 1
            self.stats["current_profile"] = profile_name
            
            print(f"🔄 音声プロファイル切替: {old_profile} → {profile_name}")
            print(f"   サンプルレート: {self.current_settings['sample_rate']}Hz")
            print(f"   チャンクサイズ: {self.current_settings['chunk_size']}")
            
        return True
    
    def get_optimized_settings(self, context: str) -> Dict[str, Any]:
        """
        コンテキストに応じた最適化設定を取得
        
        Args:
            context: 使用コンテキスト ("wake_word", "command", "conversation")
            
        Returns:
            最適化された音声設定
        """
        # コンテキストに応じてプロファイルを自動選択
        profile_map = {
            "wake_word_detection": "wake_word",
            "command_recognition": "command", 
            "conversation": "conversation",
            "default": "conversation"
        }
        
        target_profile = profile_map.get(context, "conversation")
        self.switch_profile(target_profile)
        
        return self.current_settings.copy()
    
    def create_audio_stream(self, 
                          context: str,
                          input_callback: Optional[callable] = None) -> pyaudio.Stream:
        """
        最適化された音声ストリームを作成
        
        Args:
            context: 使用コンテキスト
            input_callback: 音声入力コールバック
            
        Returns:
            PyAudioストリーム
        """
        settings = self.get_optimized_settings(context)
        
        try:
            stream = self.audio_interface.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=settings["sample_rate"],
                input=True,
                frames_per_buffer=settings["chunk_size"],
                stream_callback=input_callback,
                start=False
            )
            
            print(f"🎤 音声ストリーム作成: {context} ({settings['sample_rate']}Hz)")
            return stream
            
        except Exception as e:
            self.logger.error(f"音声ストリーム作成エラー: {e}")
            raise
    
    def resample_audio(self, 
                      audio_data: np.ndarray, 
                      source_rate: int, 
                      target_rate: int) -> np.ndarray:
        """
        音声データのリサンプリング
        
        Args:
            audio_data: 音声データ
            source_rate: 元のサンプルレート
            target_rate: 目標サンプルレート
            
        Returns:
            リサンプリングされた音声データ
        """
        if source_rate == target_rate:
            return audio_data
        
        # シンプルなリサンプリング（線形補間）
        duration = len(audio_data) / source_rate
        target_length = int(duration * target_rate)
        
        # インデックス配列を作成
        source_indices = np.linspace(0, len(audio_data) - 1, target_length)
        
        # 線形補間
        resampled = np.interp(source_indices, np.arange(len(audio_data)), audio_data)
        
        return resampled.astype(audio_data.dtype)
    
    def optimize_for_wake_word(self) -> Dict[str, Any]:
        """ウェイクワード検出用に最適化"""
        return self.get_optimized_settings("wake_word_detection")
    
    def optimize_for_command(self) -> Dict[str, Any]:
        """コマンド認識用に最適化"""
        return self.get_optimized_settings("command_recognition")
    
    def optimize_for_conversation(self) -> Dict[str, Any]:
        """会話用に最適化"""
        return self.get_optimized_settings("conversation")
    
    def measure_processing_time(self, profile_name: str, processing_time: float):
        """
        プロファイル別の処理時間を記録
        
        Args:
            profile_name: プロファイル名
            processing_time: 処理時間
        """
        if profile_name not in self.stats["processing_time_by_profile"]:
            self.stats["processing_time_by_profile"][profile_name] = []
        
        self.stats["processing_time_by_profile"][profile_name].append(processing_time)
        
        # 最新10件のみ保持
        if len(self.stats["processing_time_by_profile"][profile_name]) > 10:
            self.stats["processing_time_by_profile"][profile_name] = \
                self.stats["processing_time_by_profile"][profile_name][-10:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        stats = self.stats.copy()
        
        # 平均処理時間を計算
        avg_times = {}
        for profile, times in stats["processing_time_by_profile"].items():
            if times:
                avg_times[profile] = sum(times) / len(times)
        
        stats["average_processing_times"] = avg_times
        stats["current_settings"] = self.current_settings.copy()
        
        return stats
    
    def auto_optimize(self, recent_performance: Dict[str, float]) -> str:
        """
        最近のパフォーマンスに基づいて自動最適化
        
        Args:
            recent_performance: 最近のパフォーマンス指標
            
        Returns:
            選択されたプロファイル名
        """
        # パフォーマンスが悪い場合は低品質プロファイルに切り替え
        avg_time = recent_performance.get("average_response_time", 0)
        
        if avg_time > 3.0:  # 3秒以上の場合
            recommended_profile = "wake_word"
            print("🚀 パフォーマンス重視モードに切替")
        elif avg_time > 1.5:  # 1.5秒以上の場合
            recommended_profile = "command" 
            print("⚖️ バランスモードに切替")
        else:
            recommended_profile = "conversation"
            print("🎯 高品質モードを維持")
        
        self.switch_profile(recommended_profile)
        return recommended_profile
    
    def cleanup(self):
        """リソースの清理"""
        try:
            self.audio_interface.terminate()
            print("🔒 動的音声品質調整システム終了")
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")


class AudioProcessingMonitor:
    """音声処理のパフォーマンスを監視するクラス"""
    
    def __init__(self, optimizer: DynamicAudioOptimizer):
        self.optimizer = optimizer
        self.monitoring = False
        self.performance_history = []
        self.monitor_thread = None
        
    def start_monitoring(self, check_interval: float = 10.0):
        """パフォーマンス監視を開始"""
        self.monitoring = True
        
        def monitor_worker():
            while self.monitoring:
                time.sleep(check_interval)
                
                if self.performance_history:
                    # 最近のパフォーマンスを分析
                    recent_data = self.performance_history[-5:]  # 最新5件
                    avg_time = sum(d["response_time"] for d in recent_data) / len(recent_data)
                    
                    # 自動最適化を実行
                    self.optimizer.auto_optimize({"average_response_time": avg_time})
        
        self.monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitor_thread.start()
        print("📊 音声処理監視開始")
    
    def record_performance(self, response_time: float, profile: str):
        """パフォーマンスデータを記録"""
        self.performance_history.append({
            "timestamp": time.time(),
            "response_time": response_time,
            "profile": profile
        })
        
        # 最新50件のみ保持
        if len(self.performance_history) > 50:
            self.performance_history = self.performance_history[-50:]
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring = False
        print("⏹️ 音声処理監視停止")
