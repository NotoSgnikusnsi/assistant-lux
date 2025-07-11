"""
音声認識モジュール
音声データをテキストに変換する機能を提供
"""

import speech_recognition as sr
import numpy as np
import soundfile as sf
import tempfile
import os
from typing import Optional


class SpeechRecognizer:
    """音声認識を管理するクラス"""
    
    def __init__(self, language: str = "ja-JP"):
        """
        初期化
        
        Args:
            language: 認識言語（ja-JP=日本語, en-US=英語）
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        
        # 認識精度の調整
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        print(f"音声認識初期化完了: 言語={language}")
    
    def recognize_from_audio_data(self, audio_data: np.ndarray, 
                                sample_rate: int = 16000) -> Optional[str]:
        """
        音声データから文字起こし
        
        Args:
            audio_data: 音声データ（NumPy配列）
            sample_rate: サンプリングレート
            
        Returns:
            認識されたテキスト（失敗時はNone）
        """
        try:
            # 一時ファイルに音声データを保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_filename = temp_file.name
            
            try:
                # 音声ファイルから認識
                with sr.AudioFile(temp_filename) as source:
                    # バックグラウンドノイズの調整
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                
                # Google Speech Recognition を使用
                text = self.recognizer.recognize_google(audio, language=self.language)
                print(f"音声認識成功: '{text}'")
                return text
                
            except sr.UnknownValueError:
                print("音声を認識できませんでした")
                return None
            except sr.RequestError as e:
                print(f"音声認識サービスエラー: {e}")
                return None
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                    
        except Exception as e:
            print(f"音声認識処理エラー: {e}")
            return None
    
    def recognize_from_microphone(self, timeout: int = 5, 
                                phrase_timeout: int = 1) -> Optional[str]:
        """
        マイクから直接音声認識
        
        Args:
            timeout: タイムアウト時間（秒）
            phrase_timeout: フレーズ終了判定時間（秒）
            
        Returns:
            認識されたテキスト（失敗時はNone）
        """
        try:
            with sr.Microphone() as source:
                print("音声認識準備中...")
                # バックグラウンドノイズの調整
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("話してください...")
                
                # 音声を録音
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            print("音声を認識中...")
            # Google Speech Recognition を使用
            text = self.recognizer.recognize_google(audio, language=self.language)
            print(f"音声認識成功: '{text}'")
            return text
            
        except sr.WaitTimeoutError:
            print("音声入力がタイムアウトしました")
            return None
        except sr.UnknownValueError:
            print("音声を認識できませんでした")
            return None
        except sr.RequestError as e:
            print(f"音声認識サービスエラー: {e}")
            return None
        except Exception as e:
            print(f"音声認識エラー: {e}")
            return None
    
    def extract_command_from_wake_word_text(self, text: str, wake_words: list = None) -> tuple[bool, str]:
        """
        ウェイクワードを含むテキストからコマンド部分を抽出
        
        Args:
            text: 認識されたテキスト
            wake_words: ウェイクワードのリスト
            
        Returns:
            (ウェイクワードが検知されたか, 抽出されたコマンド)
        """
        if wake_words is None:
            # デフォルトのウェイクワード - アシスタント名「ルクス」
            wake_words = [
                "ルクス", "るくす", "Lux", "lux", "LUX"
            ]
        
        if not text:
            return False, ""
            
        text_lower = text.lower()
        
        # 1. 完全一致チェック
        for wake_word in wake_words:
            wake_word_lower = wake_word.lower()
            if wake_word_lower in text_lower:
                print(f"ウェイクワード検知（完全一致）: '{wake_word}' in '{text}'")
                return self._extract_command_after_wake_word(text, wake_word)
        
        # 2. 曖昧一致チェック（音声認識の誤認識対策）
        fuzzy_matches = {
            # 「ルクス」の誤認識されやすいパターン
            "ラックス": ["ルクス", "るくす"],
            "らっくす": ["ルクス", "るくす"],  
            "ルックス": ["ルクス", "るくす"],
            "るっくす": ["ルクス", "るくす"],
            "luck": ["Lux", "lux"],
            "LUCK": ["Lux", "LUX"],
            "lacks": ["Lux", "lux"],
        }
        
        for recognized_word, possible_wake_words in fuzzy_matches.items():
            if recognized_word.lower() in text_lower:
                # 対応するウェイクワードの中から最初のものを使用
                matched_wake_word = possible_wake_words[0]
                print(f"ウェイクワード検知（曖昧一致）: '{recognized_word}' → '{matched_wake_word}' in '{text}'")
                return self._extract_command_after_wake_word(text, recognized_word)
        
        return False, ""
    
    def _extract_command_after_wake_word(self, text: str, wake_word: str) -> tuple[bool, str]:
        """
        ウェイクワード後のコマンドを抽出するヘルパーメソッド
        """
        text_lower = text.lower()
        wake_word_lower = wake_word.lower()
        
        # ウェイクワードの位置を特定
        wake_word_positions = []
        for i in range(len(text)):
            if text[i:i+len(wake_word)].lower() == wake_word_lower:
                wake_word_positions.append(i)
        
        if wake_word_positions:
            # 最初に見つかったウェイクワードの位置を使用
            wake_word_end = wake_word_positions[0] + len(wake_word)
            command = text[wake_word_end:].strip()
            
            # 句読点や接続詞を除去
            command = command.lstrip('、。，,')
            
            print(f"抽出されたコマンド: '{command}'")
            return True, command
        
        return True, ""
    
    def is_wake_word(self, text: str, wake_words: list = None) -> bool:
        """
        ウェイクワードの検知（後方互換性のため残す）
        
        Args:
            text: 認識されたテキスト
            wake_words: ウェイクワードのリスト
            
        Returns:
            ウェイクワードが検知されたかどうか
        """
        found, _ = self.extract_command_from_wake_word_text(text, wake_words)
        return found


def test_speech_recognition():
    """音声認識のテスト関数"""
    print("=== 音声認識テスト ===")
    
    # 音声認識初期化
    recognizer = SpeechRecognizer()
    
    try:
        print("\n1. マイクからの音声認識テスト")
        print("5秒以内に何か話してください...")
        
        text = recognizer.recognize_from_microphone(timeout=5)
        if text:
            print(f"認識結果: {text}")
            
            # ウェイクワード検知テスト
            if recognizer.is_wake_word(text):
                print("-> ウェイクワードが検知されました！")
            else:
                print("-> ウェイクワードは検知されませんでした")
        
    except Exception as e:
        print(f"テストエラー: {e}")


if __name__ == "__main__":
    test_speech_recognition()
