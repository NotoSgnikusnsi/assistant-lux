"""
効果音システム
ウェイクワード検知などのイベント時に効果音を再生
"""

import numpy as np
import threading
import time
from typing import Optional, Dict, Any
import logging

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class SoundEffectPlayer:
    """効果音再生クラス"""
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 volume: float = 0.5,
                 enable_effects: bool = True):
        """
        初期化
        
        Args:
            sample_rate: サンプリングレート
            volume: 音量（0.0-1.0）
            enable_effects: 効果音を有効にするか
        """
        self.sample_rate = sample_rate
        self.volume = volume
        self.enable_effects = enable_effects
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 再生システムの選択と初期化
        self.player_type = self._select_audio_player()
        self._init_audio_player()
        
        # 事前生成済み効果音
        self.preloaded_sounds = {}
        self._generate_default_sounds()
        
        print(f"効果音システム初期化完了: {self.player_type}, 音量={volume}")
    
    def _select_audio_player(self) -> str:
        """最適な音声再生システムを選択"""
        if PYAUDIO_AVAILABLE:
            return "pyaudio"
        elif WINSOUND_AVAILABLE:
            return "winsound"
        elif PYGAME_AVAILABLE:
            return "pygame"
        else:
            return "none"
    
    def _init_audio_player(self):
        """音声再生システムの初期化"""
        try:
            if self.player_type == "pygame":
                pygame.mixer.init(
                    frequency=self.sample_rate,
                    size=-16,
                    channels=1,
                    buffer=512
                )
                self.logger.info("Pygame mixer 初期化完了")
            
            elif self.player_type == "pyaudio":
                self.pyaudio_instance = pyaudio.PyAudio()
                self.logger.info("PyAudio 初期化完了")
            
            elif self.player_type == "winsound":
                # winsoundは初期化不要
                self.logger.info("WinSound 使用")
            
        except Exception as e:
            self.logger.error(f"音声再生システム初期化エラー: {e}")
            self.player_type = "none"
    
    def _generate_default_sounds(self):
        """デフォルト効果音を生成"""
        try:
            # ウェイクワード検知音（上昇トーン）
            self.preloaded_sounds['wake_word_detected'] = self._generate_chirp_sound(
                start_freq=800, end_freq=1200, duration=0.2
            )
            
            # コマンド受付音（単純なビープ）
            self.preloaded_sounds['command_accepted'] = self._generate_beep_sound(
                frequency=1000, duration=0.15
            )
            
            # エラー音（下降トーン）
            self.preloaded_sounds['error'] = self._generate_chirp_sound(
                start_freq=1000, end_freq=500, duration=0.3
            )
            
            # 成功音（上昇→下降）
            self.preloaded_sounds['success'] = self._generate_success_sound()
            
            self.logger.info("デフォルト効果音生成完了")
            
        except Exception as e:
            self.logger.error(f"効果音生成エラー: {e}")
    
    def _generate_beep_sound(self, frequency: float, duration: float) -> np.ndarray:
        """ビープ音を生成"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # サイン波にエンベロープを適用
        wave = np.sin(2 * np.pi * frequency * t)
        # フェードイン・フェードアウト
        fade_samples = int(0.01 * self.sample_rate)  # 10msのフェード
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return (wave * self.volume * 32767).astype(np.int16)
    
    def _generate_chirp_sound(self, start_freq: float, end_freq: float, duration: float) -> np.ndarray:
        """周波数が変化する音を生成（ピコン音など）"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # 線形に周波数が変化
        freq_sweep = np.linspace(start_freq, end_freq, len(t))
        phase = np.cumsum(2 * np.pi * freq_sweep / self.sample_rate)
        wave = np.sin(phase)
        
        # エンベロープ（Attack-Decay）
        envelope = np.exp(-3 * t / duration)  # 指数減衰
        wave *= envelope
        
        return (wave * self.volume * 32767).astype(np.int16)
    
    def _generate_success_sound(self) -> np.ndarray:
        """成功音（2音の組み合わせ）"""
        # 第1音（短い上昇音）
        sound1 = self._generate_chirp_sound(600, 900, 0.1)
        # 小さな間隔
        silence = np.zeros(int(0.05 * self.sample_rate), dtype=np.int16)
        # 第2音（短い上昇音、高め）
        sound2 = self._generate_chirp_sound(900, 1200, 0.1)
        
        return np.concatenate([sound1, silence, sound2])
    
    def play_effect(self, effect_name: str, async_play: bool = True) -> bool:
        """
        効果音を再生
        
        Args:
            effect_name: 効果音名（'wake_word_detected', 'command_accepted', 'error', 'success'）
            async_play: 非同期再生するか
            
        Returns:
            再生成功フラグ
        """
        if not self.enable_effects:
            return True
        
        if effect_name not in self.preloaded_sounds:
            self.logger.warning(f"効果音 '{effect_name}' が見つかりません")
            return False
        
        if async_play:
            thread = threading.Thread(
                target=self._play_sound_data,
                args=(self.preloaded_sounds[effect_name],),
                daemon=True
            )
            thread.start()
            return True
        else:
            return self._play_sound_data(self.preloaded_sounds[effect_name])
    
    def _play_sound_data(self, sound_data: np.ndarray) -> bool:
        """音声データを再生"""
        try:
            if self.player_type == "pygame":
                return self._play_with_pygame(sound_data)
            elif self.player_type == "pyaudio":
                return self._play_with_pyaudio(sound_data)
            elif self.player_type == "winsound":
                return self._play_with_winsound(sound_data)
            else:
                self.logger.warning("音声再生システムが利用できません")
                return False
                
        except Exception as e:
            self.logger.error(f"効果音再生エラー: {e}")
            return False
    
    def _play_with_pygame(self, sound_data: np.ndarray) -> bool:
        """Pygameで音声再生"""
        try:
            # Pygameのミキサー設定に合わせて配列を調整
            # モノラル（channels=1）なので1次元配列のまま使用
            if sound_data.ndim > 1:
                sound_data = sound_data.flatten()
            
            # NumPy配列をPygameのSoundオブジェクトに変換
            sound = pygame.sndarray.make_sound(sound_data)
            sound.play()
            return True
        except Exception as e:
            self.logger.error(f"Pygame再生エラー: {e}")
            return False
    
    def _play_with_pyaudio(self, sound_data: np.ndarray) -> bool:
        """PyAudioで音声再生"""
        try:
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
            stream.write(sound_data.tobytes())
            stream.stop_stream()
            stream.close()
            return True
        except Exception as e:
            self.logger.error(f"PyAudio再生エラー: {e}")
            return False
    
    def _play_with_winsound(self, sound_data: np.ndarray) -> bool:
        """WinSoundで音声再生（簡易版）"""
        try:
            # 単純なビープ音のみ対応
            winsound.Beep(1000, 200)  # 1000Hz, 200ms
            return True
        except Exception as e:
            self.logger.error(f"WinSound再生エラー: {e}")
            return False
    
    def play_wake_word_detected(self) -> bool:
        """ウェイクワード検知効果音を再生"""
        return self.play_effect('wake_word_detected', async_play=True)
    
    def play_command_accepted(self) -> bool:
        """コマンド受付効果音を再生"""
        return self.play_effect('command_accepted', async_play=True)
    
    def play_error(self) -> bool:
        """エラー効果音を再生"""
        return self.play_effect('error', async_play=True)
    
    def play_success(self) -> bool:
        """成功効果音を再生"""
        return self.play_effect('success', async_play=True)
    
    def set_volume(self, volume: float):
        """音量を設定"""
        self.volume = max(0.0, min(1.0, volume))
        # 事前生成音を再生成
        if self.enable_effects:
            self._generate_default_sounds()
    
    def set_enabled(self, enabled: bool):
        """効果音の有効/無効を切り替え"""
        self.enable_effects = enabled
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.player_type == "pyaudio" and hasattr(self, 'pyaudio_instance'):
                self.pyaudio_instance.terminate()
            elif self.player_type == "pygame":
                pygame.mixer.quit()
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")


def test_sound_effects():
    """効果音システムのテスト"""
    print("🔊 効果音システムテスト開始")
    print("=" * 50)
    
    # 効果音プレイヤー初期化
    player = SoundEffectPlayer(volume=0.7)
    
    test_sounds = [
        ('wake_word_detected', 'ウェイクワード検知音'),
        ('command_accepted', 'コマンド受付音'),
        ('success', '成功音'),
        ('error', 'エラー音')
    ]
    
    for effect_name, description in test_sounds:
        print(f"\n🎵 {description} を再生...")
        success = player.play_effect(effect_name, async_play=False)
        print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")
        time.sleep(1)  # 音の間隔
    
    print("\n✅ 効果音テスト完了")
    player.cleanup()


if __name__ == "__main__":
    test_sound_effects()
