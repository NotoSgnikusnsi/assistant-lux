"""
音声出力診断スクリプト
"""

import pyttsx3
import time

def test_audio_output():
    print("=== 音声出力診断テスト ===")
    
    try:
        # TTSエンジン初期化
        engine = pyttsx3.init()
        
        # 現在の設定表示
        print(f"音量: {engine.getProperty('volume')}")
        print(f"速度: {engine.getProperty('rate')}")
        
        voices = engine.getProperty('voices')
        current_voice = engine.getProperty('voice')
        print(f"現在の音声: {current_voice}")
        
        # 音量を最大に設定
        engine.setProperty('volume', 1.0)
        
        # テスト音声1（短い）
        print("\n--- テスト1: 短いメッセージ ---")
        print("再生中: 'テスト'")
        engine.say("テスト")
        engine.runAndWait()
        print("再生完了")
        
        time.sleep(1)
        
        # テスト音声2（長い）
        print("\n--- テスト2: 長いメッセージ ---")
        test_message = "これは音声出力のテストです。この音声が聞こえる場合は、音声システムが正常に動作しています。"
        print(f"再生中: '{test_message}'")
        engine.say(test_message)
        engine.runAndWait()
        print("再生完了")
        
        time.sleep(1)
        
        # テスト音声3（英語）
        print("\n--- テスト3: 英語メッセージ ---")
        english_message = "Hello, this is an audio test. Can you hear this message?"
        print(f"再生中: '{english_message}'")
        
        # 英語音声に切り替え
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)  # 英語音声
        
        engine.say(english_message)
        engine.runAndWait()
        print("再生完了")
        
        print("\n=== 診断完了 ===")
        print("音声が聞こえない場合は以下を確認してください:")
        print("1. スピーカー/ヘッドフォンの接続")
        print("2. Windowsの音量設定")
        print("3. 音声出力デバイスの設定")
        print("4. 他のアプリケーションでの音声再生テスト")
        
    except Exception as e:
        print(f"音声テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_output()
