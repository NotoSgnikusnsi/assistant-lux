#!/usr/bin/env python3
"""
音声出力修正テスト
キャッシュ再生問題の修正確認
"""

import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_audio_output():
    """音声出力のテスト"""
    try:
        from src.audio_output import AudioOutputHandler
        
        print("🔍 音声出力テスト開始")
        print("=" * 50)
        
        # 音声出力初期化（キャッシュなし）
        handler = AudioOutputHandler(
            rate=200,
            volume=0.9,
            cache_phrases=None  # キャッシュ無効
        )
        
        print("✅ AudioOutputHandler初期化完了")
        
        # テスト音声
        test_texts = [
            "はい、何でしょうか？",
            "テスト音声です",
            "音声出力が正常に動作しています"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n🔊 テスト {i}: '{text}'")
            result = handler.speak_text(text, blocking=True)
            print(f"結果: {'✅ 成功' if result else '❌ 失敗'}")
            
            if not result:
                print("⚠️ 音声再生に失敗しました")
                return False
        
        print("\n✅ すべての音声テストが成功しました")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 音声出力修正テスト開始")
    success = test_audio_output()
    
    if success:
        print("\n🎉 音声出力修正が成功しました！")
    else:
        print("\n⚠️ 音声出力に問題があります。ログを確認してください。")
