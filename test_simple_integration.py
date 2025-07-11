#!/usr/bin/env python3
"""
ContinuousSpeechMonitorの簡素化テスト
"""

import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """インポートテスト"""
    print("🔍 個別モジュールのインポートテスト")
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition インポート成功")
        print(f"   バージョン: {getattr(sr, '__version__', 'unknown')}")
        
        recognizer = sr.Recognizer()
        print("✅ sr.Recognizer() 初期化成功")
        
    except Exception as e:
        print(f"❌ speech_recognition エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        import pyaudio
        print("✅ pyaudio インポート成功")
    except Exception as e:
        print(f"⚠️ pyaudio 警告: {e}")
    
    try:
        import webrtcvad
        print("✅ webrtcvad インポート成功")
    except Exception as e:
        print(f"⚠️ webrtcvad 警告: {e}")
    
    try:
        from phonetic_similarity import EnhancedWakeWordVerifier
        print("✅ phonetic_similarity インポート成功")
    except Exception as e:
        print(f"❌ phonetic_similarity エラー: {e}")
        return False
    
    print("\n🔍 ContinuousSpeechMonitorのインポートテスト")
    
    try:
        from continuous_speech import ContinuousSpeechMonitor
        print("✅ ContinuousSpeechMonitor インポート成功")
        
        # 軽量化された初期化（音声デバイスなし）
        try:
            monitor = ContinuousSpeechMonitor()
            print("✅ ContinuousSpeechMonitor 初期化成功")
            
            # 音韻的検証機能の確認
            if hasattr(monitor, 'phonetic_verifier') and monitor.phonetic_verifier is not None:
                print("✅ 音韻的検証機能が有効")
                
                # 簡単なテスト
                result = monitor._check_wake_word("ルクス今日の天気は？")
                print(f"✅ ウェイクワード検知テスト: {result}")
                
                return True
            else:
                print("⚠️ 音韻的検証機能が無効")
                return False
                
        except Exception as e:
            print(f"❌ ContinuousSpeechMonitor 初期化エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ ContinuousSpeechMonitor インポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 簡素化された統合テスト開始")
    print("=" * 50)
    
    success = test_imports()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 テスト成功！音韻的類似度検証システムが統合されています。")
    else:
        print("⚠️ テスト失敗。詳細を確認してください。")
