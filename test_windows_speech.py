"""
Windows Speech API直接テスト
"""

import win32com.client
import time

def test_windows_sapi():
    print("=== Windows SAPI直接テスト ===")
    
    try:
        # Windows Speech APIを直接使用
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        print("利用可能な音声:")
        voices = speaker.GetVoices()
        for i in range(voices.Count):
            voice = voices.Item(i)
            print(f"{i}: {voice.GetDescription()}")
        
        # 日本語音声を設定
        for i in range(voices.Count):
            voice = voices.Item(i)
            desc = voice.GetDescription()
            if "Japanese" in desc or "Haruka" in desc:
                speaker.Voice = voice
                print(f"選択された音声: {desc}")
                break
        
        # テスト音声
        test_texts = [
            "こんにちは",
            "音声テストです",
            "今日の天気は晴れです",
            "音声アシスタント ルクス です"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nテスト {i}: '{text}' を再生...")
            speaker.Speak(text)
            print("再生完了")
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"Windows SAPI エラー: {e}")
        return False

if __name__ == "__main__":
    test_windows_sapi()
