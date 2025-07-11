"""
音声入力モジュール
マイクからの音声入力と録音機能を提供
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import threading
import time
from typing import Optional, Callable


class AudioInputHandler:
    """音声入力を管理するクラス"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 recording_duration: int = 10):
        """
        初期化
        
        Args:
            sample_rate: サンプリングレート
            channels: チャンネル数（1=モノラル）
            chunk_size: オーディオチャンクサイズ
            recording_duration: 録音時間上限（秒）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.recording_duration = recording_duration
        
        # 録音データ保存用
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recorded_data = []
        
        print(f"音声入力初期化完了: {sample_rate}Hz, {channels}ch")
        
    def get_available_devices(self):
        """利用可能なオーディオデバイスを取得"""
        devices = sd.query_devices()
        print("\n=== 利用可能なオーディオデバイス ===")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:  # 入力可能なデバイスのみ
                print(f"{i}: {device['name']} (入力: {device['max_input_channels']}ch)")
        return devices
    
    def audio_callback(self, indata, frames, time, status):
        """音声入力のコールバック関数"""
        if status:
            print(f"音声入力エラー: {status}")
        
        if self.is_recording:
            # 音声データをキューに追加
            self.audio_queue.put(indata.copy())
    
    def start_monitoring(self, volume_threshold: float = 0.01):
        """音声レベルの監視を開始"""
        print("音声監視を開始しています...")
        print("何か話してください（Ctrl+Cで終了）")
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self.audio_callback,
                blocksize=self.chunk_size
            ):
                while True:
                    time.sleep(0.1)
                    # 簡単な音声レベル表示
                    if not self.audio_queue.empty():
                        data = self.audio_queue.get()
                        volume = np.sqrt(np.mean(data**2))
                        if volume > volume_threshold:
                            print(f"音声検知: {volume:.4f}")
                            
        except KeyboardInterrupt:
            print("\n音声監視を終了します")
    
    def record_audio(self, duration: Optional[int] = None) -> np.ndarray:
        """
        音声を録音
        
        Args:
            duration: 録音時間（秒）。Noneの場合はデフォルト時間
            
        Returns:
            録音された音声データ
        """
        if duration is None:
            duration = self.recording_duration
            
        print(f"録音開始: {duration}秒間録音します...")
        
        # 録音データクリア
        self.recorded_data = []
        self.is_recording = True
        
        # 録音タイマー
        def stop_recording():
            time.sleep(duration)
            self.is_recording = False
            print("録音終了")
        
        timer_thread = threading.Thread(target=stop_recording)
        timer_thread.start()
        
        # 音声ストリーム開始
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.audio_callback,
            blocksize=self.chunk_size
        ):
            # 録音中の処理
            while self.is_recording:
                try:
                    # キューからデータを取得
                    data = self.audio_queue.get(timeout=0.1)
                    self.recorded_data.append(data)
                except queue.Empty:
                    continue
        
        timer_thread.join()
        
        # 録音データを結合
        if self.recorded_data:
            audio_data = np.concatenate(self.recorded_data, axis=0)
            print(f"録音完了: {len(audio_data)/self.sample_rate:.2f}秒")
            return audio_data
        else:
            print("録音データがありません")
            return np.array([])
    
    def save_audio(self, audio_data: np.ndarray, filename: str):
        """音声データをファイルに保存"""
        try:
            sf.write(filename, audio_data, self.sample_rate)
            print(f"音声ファイル保存: {filename}")
        except Exception as e:
            print(f"音声ファイル保存エラー: {e}")
    
    def detect_silence(self, audio_data: np.ndarray, 
                      silence_threshold: float = 0.01,
                      silence_duration: float = 2.0) -> bool:
        """
        無音を検知
        
        Args:
            audio_data: 音声データ
            silence_threshold: 無音の閾値
            silence_duration: 無音と判定する継続時間（秒）
            
        Returns:
            無音が検知されたかどうか
        """
        # 音声レベルの計算
        frame_length = int(self.sample_rate * 0.1)  # 0.1秒フレーム
        silence_frames = int(silence_duration / 0.1)
        
        consecutive_silence = 0
        
        for i in range(0, len(audio_data), frame_length):
            frame = audio_data[i:i+frame_length]
            if len(frame) > 0:
                volume = np.sqrt(np.mean(frame**2))
                if volume < silence_threshold:
                    consecutive_silence += 1
                    if consecutive_silence >= silence_frames:
                        return True
                else:
                    consecutive_silence = 0
        
        return False


def test_audio_input():
    """音声入力のテスト関数"""
    print("=== 音声入力テスト ===")
    
    # オーディオハンドラー初期化
    audio_handler = AudioInputHandler()
    
    # 利用可能デバイス表示
    audio_handler.get_available_devices()
    
    try:
        print("\n1. 音声監視テスト（10秒間）")
        # 短時間の監視テスト
        audio_handler.start_monitoring()
        
    except KeyboardInterrupt:
        print("\nテストを終了します")


if __name__ == "__main__":
    test_audio_input()
