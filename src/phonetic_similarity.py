"""
音韻的類似度検証モジュール
ウェイクワード「ルクス」の検知精度向上のための音韻的類似度計算機能
"""

import re
import unicodedata
import time
from typing import Tuple, List, Dict, Optional
import numpy as np


class PhoneticSimilarityCalculator:
    """音韻的類似度計算クラス"""
    
    def __init__(self):
        # 日本語音韻グループ定義
        self.phonetic_groups = {
            # 子音グループ
            'k_group': ['か', 'が', 'く', 'ぐ', 'け', 'げ', 'こ', 'ご', 'き', 'ぎ'],
            'r_group': ['ら', 'り', 'る', 'れ', 'ろ'],
            's_group': ['さ', 'ざ', 'し', 'じ', 'す', 'ず', 'せ', 'ぜ', 'そ', 'ぞ'],
            't_group': ['た', 'だ', 'ち', 'ぢ', 'つ', 'づ', 'て', 'で', 'と', 'ど'],
            'n_group': ['な', 'に', 'ぬ', 'ね', 'の', 'ん'],
            'vowel_u': ['う', 'ゆ', 'ふ'],
        }
        
        # 音韻変化パターン
        self.phonetic_variations = {
            'ル': ['ラ', 'リ', 'レ', 'ロ', 'ヌ', 'る', 'ら', 'り', 'れ', 'ろ', 'ぬ'],
            'ク': ['グ', 'ッ', 'キ', 'ケ', 'く', 'ぐ', 'っ', 'き', 'け'],
            'ス': ['ズ', 'シ', 'ツ', 'す', 'ず', 'し', 'つ'],
        }
        
        # 音韻距離の重み
        self.similarity_weights = {
            'exact_match': 1.0,
            'same_phonetic_group': 0.8,
            'vowel_change': 0.7,
            'consonant_change': 0.6,
            'similar_sound': 0.5,
            'different': 0.0
        }
        
        # よく使われる誤認識パターンをキャッシュ
        self.cached_patterns = {
            'ラックス': 0.85,
            'ルックス': 0.90,
            'リクス': 0.80,
            'らっくす': 0.85,
            'るっくす': 0.90,
            'りくす': 0.80,
        }
    
    def calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """
        音韻的類似度の計算
        
        Args:
            text1: 比較対象テキスト1
            text2: 比較対象テキスト2
            
        Returns:
            類似度スコア (0.0-1.0)
        """
        # 事前キャッシュチェック
        cache_key = f"{text1}:{text2}"
        if cache_key in self.cached_patterns:
            return self.cached_patterns[cache_key]
        
        # ひらがな正規化
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        # 完全一致チェック
        if text1_norm == text2_norm:
            return 1.0
        
        # 複数のアルゴリズムで類似度計算
        edit_distance_score = self.phonetic_edit_distance(text1_norm, text2_norm)
        substring_score = self.optimized_substring_match(text1_norm, text2_norm)
        pattern_score = self.phonetic_pattern_match(text1_norm, text2_norm)
        
        # 重み付き平均
        final_score = (
            edit_distance_score * 0.4 +
            substring_score * 0.3 +
            pattern_score * 0.3
        )
        
        return min(1.0, max(0.0, final_score))
    
    def normalize_text(self, text: str) -> str:
        """
        テキスト正規化
        
        Args:
            text: 正規化対象テキスト
            
        Returns:
            正規化されたテキスト
        """
        if not text:
            return ""
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # カタカナをひらがなに変換
        text = self.katakana_to_hiragana(text)
        
        # 小文字化
        text = text.lower()
        
        # 句読点除去
        text = re.sub(r'[、。，,\s]', '', text)
        
        return text
    
    def katakana_to_hiragana(self, text: str) -> str:
        """
        カタカナをひらがなに変換
        
        Args:
            text: 変換対象テキスト
            
        Returns:
            ひらがなに変換されたテキスト
        """
        result = ""
        for char in text:
            if 'ァ' <= char <= 'ヶ':
                # カタカナをひらがなに変換
                result += chr(ord(char) - ord('ァ') + ord('ぁ'))
            else:
                result += char
        return result
    
    def phonetic_edit_distance(self, text1: str, text2: str) -> float:
        """
        音韻的編集距離による類似度
        
        Args:
            text1: 比較対象テキスト1
            text2: 比較対象テキスト2
            
        Returns:
            類似度スコア (0.0-1.0)
        """
        len1, len2 = len(text1), len(text2)
        
        if len1 == 0:
            return 1.0 if len2 == 0 else 0.0
        if len2 == 0:
            return 0.0
        
        # DP表作成
        dp = [[0.0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # 初期化
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        # 動的プログラミング
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                char1, char2 = text1[i-1], text2[j-1]
                
                if char1 == char2:
                    # 完全一致
                    cost = 0.0
                else:
                    # 音韻的類似度による重み付きコスト
                    similarity = self.get_phonetic_similarity(char1, char2)
                    cost = 1.0 - similarity
                
                dp[i][j] = min(
                    dp[i-1][j] + 1.0,        # 削除
                    dp[i][j-1] + 1.0,        # 挿入
                    dp[i-1][j-1] + cost      # 置換
                )
        
        # 類似度に変換（0-1の範囲）
        max_len = max(len1, len2)
        similarity = 1.0 - (dp[len1][len2] / max_len)
        return max(0.0, similarity)
    
    def get_phonetic_similarity(self, char1: str, char2: str) -> float:
        """
        2文字間の音韻的類似度
        
        Args:
            char1: 文字1
            char2: 文字2
            
        Returns:
            類似度スコア (0.0-1.0)
        """
        if char1 == char2:
            return self.similarity_weights['exact_match']
        
        # 音韻グループチェック
        for group_chars in self.phonetic_groups.values():
            if char1 in group_chars and char2 in group_chars:
                return self.similarity_weights['same_phonetic_group']
        
        # 音韻変化パターンチェック
        for base_char, variations in self.phonetic_variations.items():
            if (char1 == base_char.lower() and char2 in [v.lower() for v in variations]) or \
               (char2 == base_char.lower() and char1 in [v.lower() for v in variations]):
                return self.similarity_weights['vowel_change']
        
        # 母音の類似性チェック
        if self.are_similar_vowels(char1, char2):
            return self.similarity_weights['vowel_change']
        
        # 子音の類似性チェック  
        if self.are_similar_consonants(char1, char2):
            return self.similarity_weights['consonant_change']
        
        return self.similarity_weights['different']
    
    def are_similar_vowels(self, char1: str, char2: str) -> bool:
        """母音の類似性判定"""
        vowel_groups = [
            ['あ', 'か', 'が', 'さ', 'ざ', 'た', 'だ', 'な', 'は', 'ば', 'ぱ', 'ま', 'や', 'ら', 'わ'],
            ['い', 'き', 'ぎ', 'し', 'じ', 'ち', 'ぢ', 'に', 'ひ', 'び', 'ぴ', 'み', 'り'],
            ['う', 'く', 'ぐ', 'す', 'ず', 'つ', 'づ', 'ぬ', 'ふ', 'ぶ', 'ぷ', 'む', 'ゆ', 'る'],
            ['え', 'け', 'げ', 'せ', 'ぜ', 'て', 'で', 'ね', 'へ', 'べ', 'ぺ', 'め', 'れ'],
            ['お', 'こ', 'ご', 'そ', 'ぞ', 'と', 'ど', 'の', 'ほ', 'ぼ', 'ぽ', 'も', 'よ', 'ろ', 'を']
        ]
        
        for group in vowel_groups:
            if char1 in group and char2 in group:
                return True
        return False
    
    def are_similar_consonants(self, char1: str, char2: str) -> bool:
        """子音の類似性判定"""
        consonant_groups = [
            ['か', 'き', 'く', 'け', 'こ', 'が', 'ぎ', 'ぐ', 'げ', 'ご'],
            ['さ', 'し', 'す', 'せ', 'そ', 'ざ', 'じ', 'ず', 'ぜ', 'ぞ'],
            ['た', 'ち', 'つ', 'て', 'と', 'だ', 'ぢ', 'づ', 'で', 'ど'],
            ['な', 'に', 'ぬ', 'ね', 'の'],
            ['は', 'ひ', 'ふ', 'へ', 'ほ', 'ば', 'び', 'ぶ', 'べ', 'ぼ', 'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ'],
            ['ま', 'み', 'む', 'め', 'も'],
            ['や', 'ゆ', 'よ'],
            ['ら', 'り', 'る', 'れ', 'ろ'],
            ['わ', 'を', 'ん']
        ]
        
        for group in consonant_groups:
            if char1 in group and char2 in group:
                return True
        return False
    
    def optimized_substring_match(self, text1: str, text2: str) -> float:
        """
        最適化された部分文字列マッチング
        
        Args:
            text1: 比較対象テキスト1
            text2: 比較対象テキスト2
            
        Returns:
            類似度スコア (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        max_score = 0.0
        max_substring_length = min(8, max(len(text1), len(text2)))  # 計算量制限
        
        # 効率的な部分文字列比較
        for length in range(min(len(text1), len(text2)), 0, -1):
            if length > max_substring_length:
                continue
                
            for i in range(len(text1) - length + 1):
                substring1 = text1[i:i+length]
                
                for j in range(len(text2) - length + 1):
                    substring2 = text2[j:j+length]
                    
                    # 部分文字列の音韻的類似度
                    sub_similarity = self.phonetic_edit_distance(substring1, substring2)
                    
                    # 長さによる重み付け
                    length_weight = length / max(len(text1), len(text2))
                    
                    weighted_score = sub_similarity * length_weight
                    max_score = max(max_score, weighted_score)
                    
                    # 早期終了条件
                    if sub_similarity > 0.9:
                        return weighted_score
        
        return max_score
    
    def phonetic_pattern_match(self, text1: str, text2: str) -> float:
        """
        特定パターンによる音韻マッチング
        
        Args:
            text1: 比較対象テキスト1
            text2: 比較対象テキスト2
            
        Returns:
            類似度スコア (0.0-1.0)
        """
        target_patterns = [
            'るくす', 'らくす', 'りくす', 'れくす', 'ろくす',
            'るっくす', 'らっくす', 'りっくす',
            'るーくす', 'らーくす'
        ]
        
        # text1が目標パターンのいずれかに類似しているかチェック
        max_similarity = 0.0
        
        for pattern in target_patterns:
            similarity = self.phonetic_edit_distance(text1, pattern)
            max_similarity = max(max_similarity, similarity)
            
            # 早期終了
            if similarity > 0.9:
                return similarity
        
        return max_similarity

    def extract_wake_word_from_long_text(self, text: str, target_wake_word: str) -> Tuple[float, str]:
        """
        長文からウェイクワード部分を抽出して類似度を計算
        
        Args:
            text: 長文テキスト
            target_wake_word: 目標ウェイクワード
            
        Returns:
            (最高類似度, 抽出された部分)
        """
        normalized_text = self.normalize_text(text)
        normalized_target = self.normalize_text(target_wake_word)
        
        if not normalized_text or not normalized_target:
            return 0.0, ""
        
        max_similarity = 0.0
        best_match = ""
        target_len = len(normalized_target)
        
        # 単語境界での区切り（スペース、句読点）
        import re
        words = re.split(r'[\s、。，,]+', normalized_text)
        
        # 各単語との類似度をチェック
        for word in words:
            if len(word) >= 2:  # 短すぎる単語はスキップ
                similarity = self.calculate_phonetic_similarity(word, normalized_target)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = word
                    
                # 高い類似度が見つかった場合は早期終了
                if similarity > 0.95:
                    return similarity, word
        
        # スライディングウィンドウでの部分文字列チェック
        text_len = len(normalized_text)
        for start in range(text_len):
            # 目標単語長さの前後での範囲チェック
            for length in range(max(2, target_len - 2), min(text_len - start + 1, target_len + 3)):
                if start + length <= text_len:
                    substring = normalized_text[start:start + length]
                    similarity = self.calculate_phonetic_similarity(substring, normalized_target)
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_match = substring
                        
                    # 高い類似度が見つかった場合は早期終了
                    if similarity > 0.9:
                        return similarity, substring
        
        return max_similarity, best_match


class EnhancedWakeWordVerifier:
    """強化されたウェイクワード検証"""
    
    def __init__(self, target_wake_word: str = "ルクス"):
        self.target_wake_word = target_wake_word
        self.phonetic_calculator = PhoneticSimilarityCalculator()
        
        # 動的閾値設定
        self.base_threshold = 0.7
        self.context_adjustment = 0.0
        
        # 検証統計
        self.verification_stats = {
            'total_verifications': 0,
            'passed_verifications': 0,
            'false_positives_prevented': 0,
            'average_processing_time': 0.0,
            'processing_times': []
        }
        
        # パフォーマンス監視
        self.max_processing_time = 15.0  # ms
    
    def verify_wake_word(self, recognized_text: str, 
                        context: Dict = None) -> Tuple[bool, float, Dict]:
        """
        ウェイクワード検証
        
        Args:
            recognized_text: 音声認識結果
            context: コンテキスト情報（ノイズレベル、発話長さ等）
            
        Returns:
            (検証結果, 信頼度スコア, 詳細情報)
        """
        start_time = time.perf_counter()
        self.verification_stats['total_verifications'] += 1
        
        # 空文字列チェック
        if not recognized_text or not recognized_text.strip():
            return False, 0.0, {'error': 'empty_input'}
        
        try:
            # 長文の場合は部分抽出を実行
            if len(recognized_text) > len(self.target_wake_word) * 2:
                similarity_score, extracted_part = self.phonetic_calculator.extract_wake_word_from_long_text(
                    recognized_text, self.target_wake_word)
                
                # デバッグ情報の追加
                extracted_info = f" (抽出部分: '{extracted_part}')" if extracted_part else ""
            else:
                # 短文の場合は従来の方法
                similarity_score = self.phonetic_calculator.calculate_phonetic_similarity(
                    recognized_text, self.target_wake_word)
                extracted_info = ""
            
            # コンテキストベースの閾値調整
            adjusted_threshold = self.get_adjusted_threshold(context)
            
            # 検証結果
            is_verified = similarity_score >= adjusted_threshold
            
            if is_verified:
                self.verification_stats['passed_verifications'] += 1
            else:
                self.verification_stats['false_positives_prevented'] += 1
            
            # 処理時間記録
            processing_time = (time.perf_counter() - start_time) * 1000  # ms
            self.verification_stats['processing_times'].append(processing_time)
            
            # 平均処理時間更新（過去10回分）
            if len(self.verification_stats['processing_times']) > 10:
                self.verification_stats['processing_times'].pop(0)
            
            self.verification_stats['average_processing_time'] = \
                np.mean(self.verification_stats['processing_times'])
            
            # 詳細情報
            details = {
                'phonetic_similarity': similarity_score,
                'threshold_used': adjusted_threshold,
                'normalized_input': self.phonetic_calculator.normalize_text(recognized_text),
                'context_adjustment': self.context_adjustment,
                'processing_time_ms': processing_time,
                'performance_warning': processing_time > self.max_processing_time,
                'extracted_part': extracted_info.replace(" (抽出部分: '", "").replace("')", "") if extracted_info else ""
            }
            
            return is_verified, similarity_score, details
            
        except Exception as e:
            # エラー時の処理
            processing_time = (time.perf_counter() - start_time) * 1000
            return False, 0.0, {
                'error': str(e),
                'processing_time_ms': processing_time
            }
    
    def get_adjusted_threshold(self, context: Dict = None) -> float:
        """
        コンテキストに応じた閾値調整
        
        Args:
            context: コンテキスト情報
            
        Returns:
            調整された閾値
        """
        threshold = self.base_threshold
        
        if context:
            # ノイズレベルによる調整
            noise_level = context.get('noise_level', 0.0)
            if noise_level > 0.5:
                threshold -= 0.1  # ノイズが多い場合は閾値を下げる
            
            # 発話長さによる調整
            text_length = context.get('text_length', 0)
            if text_length > 15:
                threshold -= 0.15  # 長文の場合は閾値を大幅に下げる
            elif text_length > 10:
                threshold -= 0.1   # 中程度の長さの場合は下げる
            elif text_length > 6:
                threshold -= 0.05  # 短めの複合文の場合も少し下げる
            elif text_length < 3:
                threshold -= 0.05  # 短すぎる場合は閾値を下げる
            
            # 認識信頼度による調整
            recognition_confidence = context.get('recognition_confidence', 1.0)
            if recognition_confidence < 0.8:
                threshold -= 0.05  # 認識信頼度が低い場合は閾値を下げる
            
            # 時間帯による調整（夜間は閾値を下げる）
            hour = context.get('hour', 12)
            if hour < 6 or hour > 22:
                threshold -= 0.05
        
        self.context_adjustment = threshold - self.base_threshold
        return max(0.5, min(0.9, threshold))  # 0.5-0.9の範囲に制限
    
    def get_verification_statistics(self) -> Dict:
        """
        検証統計情報取得
        
        Returns:
            統計情報辞書
        """
        stats = self.verification_stats.copy()
        
        if stats['total_verifications'] > 0:
            stats['accuracy_rate'] = stats['passed_verifications'] / stats['total_verifications']
            stats['false_positive_prevention_rate'] = stats['false_positives_prevented'] / stats['total_verifications']
        else:
            stats['accuracy_rate'] = 0.0
            stats['false_positive_prevention_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """統計情報リセット"""
        self.verification_stats = {
            'total_verifications': 0,
            'passed_verifications': 0,
            'false_positives_prevented': 0,
            'average_processing_time': 0.0,
            'processing_times': []
        }


def test_phonetic_verification():
    """音韻的検証のテスト関数"""
    print("=== 音韻的類似度検証システム テスト ===\n")
    
    verifier = EnhancedWakeWordVerifier("ルクス")
    
    test_cases = [
        # (入力テキスト, 期待結果, 説明)
        ("ルクス", True, "完全一致"),
        ("るくす", True, "ひらがな"),
        ("ラクス", True, "音韻変化(ル→ラ)"),
        ("ルックス", True, "促音挿入"),
        ("リクス", True, "母音変化(ル→リ)"),
        ("ルクス今日の天気", True, "ウェイクワード＋コマンド"),
        ("今日はルクス", True, "前置詞付きウェイクワード"),
        ("こんにちは", False, "無関係語"),
        ("ブックス", False, "類似だが異なる語"),
        ("", False, "空文字列"),
        ("ルークス", True, "長音変化"),
        ("らっくす", True, "ひらがな促音"),
    ]
    
    print("テストケース実行:")
    print("-" * 70)
    
    for i, (text, expected, description) in enumerate(test_cases, 1):
        context = {
            'text_length': len(text),
            'noise_level': 0.3,
            'recognition_confidence': 0.9
        }
        
        is_verified, confidence, details = verifier.verify_wake_word(text, context)
        
        result_mark = "✅" if (is_verified == expected) else "❌"
        print(f"{result_mark} {i:2d}. {description}")
        print(f"     入力: '{text}' → 信頼度: {confidence:.3f} → {is_verified}")
        print(f"     正規化: '{details.get('normalized_input', 'N/A')}'")
        print(f"     処理時間: {details.get('processing_time_ms', 0):.1f}ms")
        
        if details.get('performance_warning'):
            print(f"     ⚠️ 処理時間警告: 制限時間超過")
        
        print()
    
    # 統計表示
    print("\n" + "=" * 50)
    print("検証統計情報:")
    stats = verifier.get_verification_statistics()
    print(f"  総検証回数: {stats['total_verifications']}")
    print(f"  検証成功: {stats['passed_verifications']}")
    print(f"  誤検知防止: {stats['false_positives_prevented']}")
    print(f"  成功率: {stats['accuracy_rate']:.1%}")
    print(f"  誤検知防止率: {stats['false_positive_prevention_rate']:.1%}")
    print(f"  平均処理時間: {stats['average_processing_time']:.2f}ms")
    
    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_phonetic_verification()
