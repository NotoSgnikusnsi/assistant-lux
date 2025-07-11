"""
音声出力の詳細診断スクリプト
"""

import pyttsx3
import time

def diagnose_audio_system():
    print("=== 音声システム詳細診断 ===")
    
    try:
        # pyttsx3エンジンの初期化
        print("1. エンジン初期化中...")
        engine = pyttsx3.init()
        print("✅ エンジン初期化成功")
        
        # 音声の詳細設定を確認
        print("\n2. 現在の音声設定:")
        voices = engine.getProperty('voices')
        current_voice = engine.getProperty('voice')
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        
        print(f"   現在の音声: {current_voice}")
        print(f"   速度: {rate}")
        print(f"   音量: {volume}")
        
        print("\n3. 利用可能な音声一覧:")
        for i, voice in enumerate(voices):
            is_current = "★" if voice.id == current_voice else " "
            print(f"   {is_current} {i}: {voice.name}")
            print(f"      ID: {voice.id}")
            print(f"      言語: {voice.languages if voice.languages else '不明'}")
            print()
        
        # 音声設定を最適化
        print("4. 音声設定を最適化中...")
        
        # 音量を最大に設定
        engine.setProperty('volume', 1.0)
        
        # 速度を調整
        engine.setProperty('rate', 150)
        
        # 日本語音声を明示的に選択
        for voice in voices:
            if voice.languages and any('ja' in lang.lower() for lang in voice.languages):
                engine.setProperty('voice', voice.id)
                print(f"   日本語音声に設定: {voice.name}")
                break
        else:
            print("   日本語音声が見つかりません、デフォルトを使用")
        
        # テスト音声 1: 短いテスト
        print("\n5. テスト 1 - 短いテスト:")
        print("   '音声テスト' を再生します...")
        engine.say("音声テスト")
        engine.runAndWait()
        print("   再生完了")
        
        # 少し待機
        time.sleep(1)
        
        # テスト音声 2: 長いテスト
        print("\n6. テスト 2 - 長いテスト:")
        test_text = "こんにちは。音声アシスタント ルクス です。音声出力が正常に動作しているかテストしています。"
        print(f"   '{test_text}' を再生します...")
        engine.say(test_text)
        engine.runAndWait()
        print("   再生完了")
        
        # テスト音声 3: 英語テスト
        print("\n7. テスト 3 - 英語テスト:")
        engine.say("Hello, this is an English test.")
        engine.runAndWait()
        print("   英語テスト完了")
        
        # エンジンを停止
        engine.stop()
        print("\n✅ 全テスト完了")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

def test_windows_speech():
    print("\n=== Windows Speech API テスト ===")
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        print("Windows Speech APIを使用してテスト:")
        speaker.Speak("Windows Speech API テストです")
        print("Windows Speech API テスト完了")
        
    except ImportError:
        print("Windows Speech API (win32com) が利用できません")
    except Exception as e:
        print(f"Windows Speech API エラー: {e}")

if __name__ == "__main__":
    diagnose_audio_system()
    test_windows_speech()
