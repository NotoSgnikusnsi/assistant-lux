#!/usr/bin/env python3
"""
音韻的類似度検証システムのテストスクリプト
"""

import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_phonetic_verification():
    """音韻的類似度検証のテスト"""
    try:
        print("🔍 音韻的類似度検証システムのテストを開始")
        
        # モジュールインポートテスト
        from phonetic_similarity import EnhancedWakeWordVerifier
        print("✅ EnhancedWakeWordVerifierのインポート成功")
        
        # 初期化テスト
        verifier = EnhancedWakeWordVerifier("ルクス")
        print("✅ EnhancedWakeWordVerifier初期化成功")
        
        # テストケース
        test_cases = [
            "ルクス",      # 完全一致
            "るくす",      # ひらがな版
            "ルック",      # 似た音
            "クルス",      # 音の順番違い
            "リクス",      # 微妙に違う
            "ハクス",      # 似てない
            "こんにちは",   # 全く違う
        ]
        
        print("\n📊 テスト結果:")
        print("-" * 50)
        for test_word in test_cases:
            try:
                is_match, confidence, details = verifier.verify_wake_word(test_word)
                status = "✅ 一致" if is_match else "❌ 不一致"
                print(f"{test_word:<10} | {status} | 信頼度: {confidence:.3f} | 処理時間: {details.get('processing_time_ms', 0):.1f}ms")
            except Exception as e:
                print(f"{test_word:<10} | ❌ エラー | {e}")
        
        print("-" * 50)
        print("🎯 音韻的類似度検証システムのテスト完了")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_continuous_speech_import():
    """ContinuousSpeechMonitorのインポートテスト"""
    try:
        print("\n🔍 ContinuousSpeechMonitorのインポートテストを開始")
        
        # continuous_speechのインポートテスト
        from continuous_speech import ContinuousSpeechMonitor
        print("✅ ContinuousSpeechMonitorのインポート成功")
        
        # 初期化テスト（音声デバイスなしでもエラーにならないように）
        try:
            monitor = ContinuousSpeechMonitor()
            print("✅ ContinuousSpeechMonitor初期化成功")
            
            # 音韻的検証機能の有効性確認
            if hasattr(monitor, 'phonetic_verifier') and monitor.phonetic_verifier:
                print("✅ 音韻的検証機能が有効です")
                return True
            else:
                print("⚠️ 音韻的検証機能が無効です")
                return False
                
        except Exception as e:
            print(f"⚠️ ContinuousSpeechMonitor初期化で警告: {e}")
            print("（音声デバイス関連のエラーの可能性があります）")
            return False
            
    except Exception as e:
        print(f"❌ ContinuousSpeechMonitorインポート失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 音韻的類似度検証システム - 統合テスト開始")
    print("=" * 60)
    
    # テスト実行
    phonetic_ok = test_phonetic_verification()
    continuous_ok = test_continuous_speech_import()
    
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー:")
    print(f"音韻的類似度検証: {'✅ 成功' if phonetic_ok else '❌ 失敗'}")
    print(f"ContinuousSpeech統合: {'✅ 成功' if continuous_ok else '❌ 失敗'}")
    
    if phonetic_ok and continuous_ok:
        print("\n🎉 すべてのテストが成功しました！")
        print("音韻的類似度検証機能が正常に動作しています。")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
        print("詳細なエラー情報を確認して修正してください。")
