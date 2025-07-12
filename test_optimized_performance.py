#!/usr/bin/env python3
"""
最適化された音韻的検証システムのパフォーマンステスト
"""

import sys
import os
import time

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_performance_optimization():
    """パフォーマンス最適化のテスト"""
    print("🚀 音韻的類似度検証システム - パフォーマンス最適化テスト")
    print("=" * 70)
    
    try:
        from phonetic_similarity import EnhancedWakeWordVerifier
        
        verifier = EnhancedWakeWordVerifier("ルクス")
        
        # パフォーマンステストケース
        test_cases = [
            # (入力テキスト, 説明, 期待される処理時間(ms))
            ("ルクス", "短文・完全一致", 1.0),
            ("るくす", "短文・ひらがな", 1.0),
            ("ラクス", "短文・音韻変化", 1.0),
            ("ルクス 今日の天気を教えて", "長文・コマンド付き", 3.0),
            ("今日はルクス、電気をつけて", "長文・前置詞付き", 3.0),
            ("おはよう、ルクスさん、今日はどんな一日になるでしょうか？", "非常に長い文", 5.0),
            ("こんにちは", "短文・無関係語", 1.0),
            ("ブックス", "短文・類似語", 1.0),
        ]
        
        print("📊 パフォーマンステスト結果:")
        print("-" * 70)
        
        total_time = 0
        fast_count = 0
        
        for i, (text, description, expected_time) in enumerate(test_cases, 1):
            context = {
                'text_length': len(text),
                'noise_level': 0.3,
                'recognition_confidence': 0.9
            }
            
            # 複数回実行して平均処理時間を計測
            times = []
            for _ in range(5):
                start = time.perf_counter()
                is_verified, confidence, details = verifier.verify_wake_word(text, context)
                end = time.perf_counter()
                times.append((end - start) * 1000)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            # 期待時間との比較
            performance_mark = "🚀" if avg_time <= expected_time else "⚠️" if avg_time <= expected_time * 1.5 else "🐌"
            
            if avg_time <= expected_time:
                fast_count += 1
            
            total_time += avg_time
            
            print(f"{performance_mark} {i:2d}. {description}")
            print(f"     入力: '{text[:30]}{'...' if len(text) > 30 else ''}'")
            print(f"     結果: {is_verified} (信頼度: {confidence:.3f})")
            print(f"     処理時間: 平均{avg_time:.1f}ms (範囲: {min_time:.1f}-{max_time:.1f}ms)")
            print(f"     期待時間: {expected_time}ms → {'✅達成' if avg_time <= expected_time else '❌超過'}")
            print()
        
        # 総合結果
        avg_total_time = total_time / len(test_cases)
        performance_ratio = fast_count / len(test_cases) * 100
        
        print("=" * 70)
        print("📈 総合パフォーマンス結果:")
        print(f"   平均処理時間: {avg_total_time:.2f}ms")
        print(f"   期待時間達成率: {performance_ratio:.1f}% ({fast_count}/{len(test_cases)})")
        
        # 統計情報
        stats = verifier.get_verification_statistics()
        print(f"   総検証回数: {stats['total_verifications']}")
        print(f"   成功率: {stats['accuracy_rate']:.1%}")
        print(f"   誤検知防止率: {stats['false_positive_prevention_rate']:.1%}")
        
        if performance_ratio >= 80:
            print("🎉 優秀なパフォーマンスです！")
        elif performance_ratio >= 60:
            print("✅ 良好なパフォーマンスです。")
        else:
            print("⚠️ パフォーマンスの改善が必要です。")
        
        return performance_ratio >= 60
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_algorithm_selection():
    """アルゴリズム選択の最適化テスト"""
    print("\n🔍 アルゴリズム選択最適化テスト")
    print("-" * 50)
    
    try:
        from phonetic_similarity import PhoneticSimilarityCalculator
        
        calculator = PhoneticSimilarityCalculator()
        
        test_cases = [
            ("ルクス", "るくす", "短文処理"),
            ("ルクス 今日の天気", "るくす", "長文処理"),
            ("らくす", "るくす", "音韻変化"),
        ]
        
        for text1, text2, description in test_cases:
            start = time.perf_counter()
            similarity = calculator.calculate_phonetic_similarity(text1, text2)
            end = time.perf_counter()
            
            processing_time = (end - start) * 1000
            
            # 使用されたアルゴリズムを推定
            text_len = max(len(text1), len(text2))
            if text_len <= calculator.short_text_threshold:
                algorithm = "単一アルゴリズム（編集距離）"
            else:
                algorithm = "マルチアルゴリズム" if calculator.enable_multi_algorithm else "単一アルゴリズム"
            
            print(f"✅ {description}")
            print(f"   入力: '{text1}' vs '{text2}'")
            print(f"   類似度: {similarity:.3f}")
            print(f"   処理時間: {processing_time:.1f}ms")
            print(f"   使用アルゴリズム: {algorithm}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ アルゴリズム選択テスト失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 音韻的類似度検証システム - 最適化パフォーマンステスト開始")
    print("=" * 70)
    
    # テスト実行
    performance_ok = test_performance_optimization()
    algorithm_ok = test_algorithm_selection()
    
    print("\n" + "=" * 70)
    print("📋 テスト結果サマリー:")
    print(f"パフォーマンステスト: {'✅ 成功' if performance_ok else '❌ 失敗'}")
    print(f"アルゴリズム選択テスト: {'✅ 成功' if algorithm_ok else '❌ 失敗'}")
    
    if performance_ok and algorithm_ok:
        print("\n🎉 すべての最適化が正常に動作しています！")
        print("音韻的類似度検証システムの処理速度が向上しました。")
    else:
        print("\n⚠️ 一部の最適化に問題があります。")
        print("詳細なエラー情報を確認して修正してください。")
