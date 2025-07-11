"""
音声出力の問題特定用シンプルテスト
"""

def test_simple_audio():
    print("=== シンプル音声テスト ===")
    
    try:
        from src.audio_output import AudioOutputHandler
        print("✅ audio_outputモジュール読み込み成功")
        
        # 音声出力ハンドラー初期化
        audio_handler = AudioOutputHandler()
        print("✅ AudioOutputHandler初期化成功")
        
        # シンプルなテスト
        test_texts = [
            "こんにちは、テストです",
            "今日の天気は晴れです",
            "音声出力は正常に動作していますか？"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n--- テスト {i} ---")
            print(f"テキスト: {text}")
            
            success = audio_handler.speak_text(text, blocking=True)
            print(f"結果: {'成功' if success else '失敗'}")
            
            if not success:
                print("❌ 音声出力に失敗しました")
                break
            
            import time
            time.sleep(1)  # 少し待機
        
        print("\n=== テスト完了 ===")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_audio()
