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

# 音韻的類似度検証モジュールのインポートを追加
try:
    from .phonetic_similarity import EnhancedWakeWordVerifier
    PHONETIC_VERIFICATION_AVAILABLE = True
except ImportError:
    try:
        from phonetic_similarity import EnhancedWakeWordVerifier
        PHONETIC_VERIFICATION_AVAILABLE = True
    except ImportError:
        PHONETIC_VERIFICATION_AVAILABLE = False
        print("⚠️ 音韻的類似度検証モジュールが見つかりません（オプション機能）")


class SpeechRecognizer:
    """音声認識を管理するクラス"""
    
    def __init__(self, language: str = "ja-JP", enable_phonetic_verification: bool = True):
        """
        初期化
        
        Args:
            language: 認識言語（ja-JP=日本語, en-US=英語）
            enable_phonetic_verification: 音韻的類似度検証を有効にするか
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        
        # 認識精度の調整（ルクス検知に最適化）
        self.recognizer.energy_threshold = 250  # 少し下げて感度向上
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6   # 短い発話も認識しやすく
        self.recognizer.phrase_threshold = 0.3  # フレーズ開始の検知を早く
        self.recognizer.non_speaking_duration = 0.3  # 無音判定を短く
        
        # 音韻的類似度検証の設定
        self.enable_phonetic_verification = enable_phonetic_verification and PHONETIC_VERIFICATION_AVAILABLE
        self.phonetic_verifier = None
        
        if self.enable_phonetic_verification:
            try:
                self.phonetic_verifier = EnhancedWakeWordVerifier()
                print(f"✅ 音韻的類似度検証機能を有効化")
            except Exception as e:
                print(f"⚠️ 音韻的類似度検証の初期化に失敗: {e}")
                self.enable_phonetic_verification = False
        
        print(f"音声認識初期化完了: 言語={language}, 音韻検証={self.enable_phonetic_verification}")
    
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
                
                # Google Speech Recognition を使用（show_allで複数候補を取得）
                text = self.recognizer.recognize_google(
                    audio, 
                    language=self.language,
                    show_all=False  # まずは最も可能性の高い結果を取得
                )
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
            # Google Speech Recognition を使用（精度向上設定）
            text = self.recognizer.recognize_google(
                audio, 
                language=self.language,
                show_all=False
            )
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
                return self._extract_command_after_wake_word(correct, "ルクス")
        
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
            "リクス": ["ルクス", "るくす"],      # 母音変化対応
            "りくす": ["ルクス", "るくす"],
            "ラクス": ["ルクス", "るくす"],      # よくある誤認識
            "らくす": ["ルクス", "るくす"],
            # 特殊な誤認識パターン（「おはようルクス」→「おはようございます」など）
            "ございます": ["ルクス", "るくす"],   # 重要：敬語への誤変換対策
            "おはようございます": ["おはようルクス", "おはようるくす"],
            "こんにちは": ["ルクス", "るくす"],   # 挨拶の誤認識対策
            "ありがとうございます": ["ルクス", "るくす"],  # 敬語誤認識対策
            # 英語パターン
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
        
        # 3. 音韻的類似度検証によるチェック
        if self.enable_phonetic_verification and self.phonetic_verifier:
            for wake_word in wake_words:
                try:
                    # 音韻的類似度検証を実行
                    is_verified, confidence, details = self.phonetic_verifier.verify_wake_word(
                        text, 
                        context={'text_length': len(text), 'recognition_confidence': 0.9}
                    )
                    if is_verified:
                        print(f"ウェイクワード検知（音韻的類似度）: '{text}' → '{wake_word}' (信頼度: {confidence:.2f})")
                        return self._extract_command_after_wake_word(text, wake_word)
                except Exception as e:
                    # 音韻的検証でエラーが発生した場合はスキップ
                    print(f"音韻的検証エラー（スキップ）: {e}")
                    pass
        
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
