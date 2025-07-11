"""
音声合成キャッシュシステム
よく使うフレーズを事前生成してキャッシュする
"""

import pyttsx3
import io
import wave
import threading
import logging
from typing import Dict, Optional, List
import os


class AudioCache:
    """音声合成結果をキャッシュするクラス"""
    
    def __init__(self, cache_phrases: List[str], voice_settings: Dict):
        """
        初期化
        
        Args:
            cache_phrases: キャッシュするフレーズのリスト
            voice_settings: 音声設定（rate, volume等）
        """
        self.cache_phrases = cache_phrases
        self.voice_settings = voice_settings
        self.audio_cache: Dict[str, bytes] = {}
        self.logger = logging.getLogger(__name__)
        
        # TTSエンジン初期化
        self.tts_engine = pyttsx3.init()
        self._configure_tts_engine()
        
        # キャッシュディレクトリ作成
        self.cache_dir = "cache/audio"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print("🔊 音声キャッシュシステム初期化開始...")
        
    def _configure_tts_engine(self):
        """TTSエンジンの設定"""
        try:
            # 音声設定を適用
            self.tts_engine.setProperty('rate', self.voice_settings.get('rate', 200))
            self.tts_engine.setProperty('volume', self.voice_settings.get('volume', 0.8))
            
            # 音声IDが指定されている場合は設定
            voice_id = self.voice_settings.get('voice_id')
            if voice_id:
                voices = self.tts_engine.getProperty('voices')
                if voice_id < len(voices):
                    self.tts_engine.setProperty('voice', voices[voice_id].id)
                    
        except Exception as e:
            self.logger.warning(f"TTS設定エラー: {e}")
    
    def pregenerate_cache(self):
        """
        キャッシュフレーズを事前生成
        """
        def generate_thread():
            for i, phrase in enumerate(self.cache_phrases):
                try:
                    # 音声ファイルパス
                    cache_file = os.path.join(self.cache_dir, f"cache_{i}.wav")
                    
                    # 既存のキャッシュファイルがあれば読み込み
                    if os.path.exists(cache_file):
                        with open(cache_file, 'rb') as f:
                            self.audio_cache[phrase] = f.read()
                        print(f"✅ キャッシュ読み込み: {phrase}")
                    else:
                        # 新規生成
                        self.tts_engine.save_to_file(phrase, cache_file)
                        self.tts_engine.runAndWait()
                        
                        # 生成されたファイルを読み込み
                        with open(cache_file, 'rb') as f:
                            self.audio_cache[phrase] = f.read()
                        print(f"🎵 音声生成完了: {phrase}")
                        
                except Exception as e:
                    self.logger.error(f"音声生成エラー ({phrase}): {e}")
            
            print(f"🚀 音声キャッシュ生成完了: {len(self.audio_cache)}/{len(self.cache_phrases)}個")
        
        # バックグラウンドで生成
        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()
        return thread
    
    def get_cached_audio(self, text: str) -> Optional[bytes]:
        """
        キャッシュされた音声データを取得
        
        Args:
            text: テキスト
            
        Returns:
            音声データ（バイト）またはNone
        """
        # 完全一致
        if text in self.audio_cache:
            return self.audio_cache[text]
        
        # 部分一致検索
        for cached_phrase in self.audio_cache:
            if cached_phrase in text or text in cached_phrase:
                return self.audio_cache[cached_phrase]
        
        return None
    
    def add_to_cache(self, text: str, audio_data: bytes):
        """
        新しい音声をキャッシュに追加
        
        Args:
            text: テキスト
            audio_data: 音声データ
        """
        self.audio_cache[text] = audio_data
        print(f"📝 キャッシュ追加: {text}")
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.audio_cache.clear()
        # キャッシュファイルも削除
        for file in os.listdir(self.cache_dir):
            if file.startswith("cache_") and file.endswith(".wav"):
                os.remove(os.path.join(self.cache_dir, file))
        print("🗑️ 音声キャッシュをクリアしました")
    
    def get_cache_stats(self) -> Dict:
        """キャッシュの統計情報を取得"""
        return {
            "cached_phrases": len(self.audio_cache),
            "total_phrases": len(self.cache_phrases),
            "cache_hit_rate": len(self.audio_cache) / len(self.cache_phrases) if self.cache_phrases else 0
        }
