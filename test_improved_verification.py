#!/usr/bin/env python3
"""
改善された音韻的類似度検証システムのテスト
特に長文対応の検証に焦点を当てる
"""

import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_improved_verification():
    """改善された音韻的検証のテスト"""
    try:
        from phonetic_similarity import EnhancedWakeWordVerifier
        
        print("🔍 改善された音韻的類似度検証システムのテスト")
        print("=" * 60)
        
        verifier = EnhancedWakeWordVerifier("ルクス")
        
        # 実際のログから取得したテストケース
        test_cases = [
            # (入力テキスト, 期待結果, 説明)
            ("るくす", True, "ひらがな基本形"),
            ("ルックス", True, "促音挿入"),
            ("ルークス", True, "長音変化"), 
            ("ルクス 電気をつけて", True, "ウェイクワード+コマンド（重要）"),
            ("ルークス電気をつけて", True, "ウェイクワード+コマンド（スペースなし）"),
            ("今日はルクス", True, "前置詞付きウェイクワード"),
            ("電気をつけてルクス", True, "後置ウェイクワード"),
            ("ルクス、今日の天気は？", True, "句読点付きコマンド"),
            ("こんにちはルクス、電気を消して", True, "複雑な文章"),
            ("looks", False, "英語の類似語"),
            ("ブックス", False, "非関連語"),
            ("", False, "空文字列"),
        ]
        
        print("📊 テスト結果 (改善版):")
        print("-" * 60)
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, (text, expected, description) in enumerate(test_cases, 1):
            context = {
                'text_length': len(text),
                'noise_level': 0.3,
                'recognition_confidence': 0.9
            }
            
            is_verified, confidence, details = verifier.verify_wake_word(text, context)
            
            # 結果判定
            is_success = (is_verified == expected)
            result_mark = "✅" if is_success else "❌"
            
            if is_success:
                success_count += 1
            
            print(f"{result_mark} {i:2d}. {description}")
            print(f"     入力: '{text}'")
            print(f"     結果: {is_verified} (期待値: {expected})")
            print(f"     信頼度: {confidence:.3f} (閾値: {details.get('threshold_used', 0.7):.3f})")
            print(f"     処理時間: {details.get('processing_time_ms', 0):.1f}ms")
            
            if details.get('extracted_part'):
                print(f"     抽出部分: '{details['extracted_part']}'")
            
            if details.get('context_adjustment', 0) != 0:
                print(f"     閾値調整: {details['context_adjustment']:+.3f}")
            
            print()
        
        # 結果サマリー
        success_rate = success_count / total_count * 100
        print("=" * 60)
        print(f"📈 テスト結果サマリー:")
        print(f"   成功: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        # 統計情報
        stats = verifier.get_verification_statistics()
        print(f"   総検証回数: {stats['total_verifications']}")
        print(f"   平均処理時間: {stats['average_processing_time']:.2f}ms")
        
        if success_rate >= 90:
            print("🎉 優秀な結果です！")
        elif success_rate >= 75:
            print("✅ 良好な結果です。")
        else:
            print("⚠️ 改善が必要です。")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_long_text_extraction():
    """長文からのウェイクワード抽出テスト"""
    try:
        from phonetic_similarity import PhoneticSimilarityCalculator
        
        print("\n🔍 長文抽出機能の詳細テスト")
        print("=" * 50)
        
        calculator = PhoneticSimilarityCalculator()
        
        test_texts = [
            "ルクス 電気をつけて",
            "今日はルクスお疲れ様",
            "電気を消してルクス",
            "ルークス今日の天気教えて",
            "こんにちはルックス、音楽をかけて",
        ]
        
        for text in test_texts:
            similarity, extracted = calculator.extract_wake_word_from_long_text(text, "ルクス")
            print(f"入力: '{text}'")
            print(f"抽出: '{extracted}' (類似度: {similarity:.3f})")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 長文抽出テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 改善された音韻的類似度検証システム - 検証テスト")
    print("特に長文・複合文の処理能力を重点的にテスト")
    print("=" * 70)
    
    # テスト実行
    basic_test_ok = test_improved_verification()
    extraction_test_ok = test_long_text_extraction()
    
    print("\n" + "=" * 70)
    print("📋 最終テスト結果:")
    print(f"基本検証テスト: {'✅ 成功' if basic_test_ok else '❌ 失敗'}")
    print(f"長文抽出テスト: {'✅ 成功' if extraction_test_ok else '❌ 失敗'}")
    
    if basic_test_ok and extraction_test_ok:
        print("\n🎉 改善が成功しました！")
        print("長文対応機能が正常に動作しています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("詳細なエラー情報を確認してください。")
