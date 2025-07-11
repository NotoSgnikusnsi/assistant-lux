"""
ルクス認識精度テスト
「おはようルクス」→「おはようございます」誤認識対策の検証
"""

from src.speech_recognizer import SpeechRecognizer
from src.continuous_speech import ContinuousSpeechMonitor
import time


def test_text_based_recognition():
    """テキストベースでの認識テスト"""
    print("=" * 50)
    print("テキストベース認識テスト")
    print("=" * 50)
    
    recognizer = SpeechRecognizer()
    
    # 問題のケースを含むテストケース
    test_cases = [
        # 正常なケース
        ("おはようルクス", True, "正常"),
        ("ルクス、今日の天気", True, "正常"),
        ("こんにちはルクス", True, "正常"),
        
        # 誤認識ケース（修正前は失敗）
        ("おはようございます", True, "挨拶誤認識修正"),
        ("こんにちは", True, "挨拶誤認識修正"),
        ("ありがとうございます", True, "敬語誤認識修正"),
        
        # 音韻的類似ケース
        ("おはようラクス", True, "音韻類似"),
        ("おはようリクス", True, "音韻類似"),
        ("ラクス、時間を教えて", True, "音韻類似"),
        ("ルックス、照明をつけて", True, "音韻類似"),
        
        # 非ウェイクワードケース
        ("今日はいい天気ですね", False, "非ウェイクワード"),
        ("おはよう", False, "非ウェイクワード"),
        ("こんばんは", True, "挨拶誤認識修正"),  # こんばんは -> ルクス
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, (text, expected_detected, test_type) in enumerate(test_cases, 1):
        is_detected, command = recognizer.extract_command_from_wake_word_text(text)
        
        # 結果判定
        success = (is_detected == expected_detected)
        if success:
            success_count += 1
            status = "✅ 成功"
        else:
            status = "❌ 失敗"
        
        print(f"{i:2d}. {status} [{test_type}] '{text}'")
        print(f"    期待値: {expected_detected}, 実際: {is_detected}, コマンド: '{command}'")
        print()
    
    print(f"結果: {success_count}/{total_count} ({success_count/total_count*100:.1f}%) 成功")
    return success_count == total_count


def test_actual_speech_recognition():
    """実際の音声認識テスト"""
    print("=" * 50)
    print("実際の音声認識テスト")
    print("=" * 50)
    
    recognizer = SpeechRecognizer()
    
    test_phrases = [
        "おはようルクス",
        "おはようございます",  # これが問題のケース
        "ルクス、今日の天気",
        "ラクス、時間を教えて",
    ]
    
    print("以下の音声を順番に試してください：")
    print("（各テストで5秒以内に発話してください）")
    print()
    
    results = []
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i}. 「{phrase}」と発話してください...")
        print("   準備ができたらEnterを押してください", end="")
        input()
        
        try:
            text = recognizer.recognize_from_microphone(timeout=5, phrase_timeout=3)
            if text:
                is_wake, command = recognizer.extract_command_from_wake_word_text(text)
                status = "✅ ウェイクワード検知" if is_wake else "❌ 検知なし"
                
                result = {
                    'phrase': phrase,
                    'recognized': text,
                    'wake_detected': is_wake,
                    'command': command
                }
                results.append(result)
                
                print(f"   認識結果: '{text}'")
                print(f"   {status}, コマンド: '{command}'")
            else:
                print("   音声が認識されませんでした")
                results.append({
                    'phrase': phrase,
                    'recognized': None,
                    'wake_detected': False,
                    'command': ''
                })
        except Exception as e:
            print(f"   エラー: {e}")
            results.append({
                'phrase': phrase,
                'recognized': None,
                'wake_detected': False,
                'command': ''
            })
        
        print()
    
    # 結果サマリー
    print("=" * 30)
    print("テスト結果サマリー")
    print("=" * 30)
    for i, result in enumerate(results, 1):
        status = "✅" if result['wake_detected'] else "❌"
        print(f"{i}. {status} '{result['phrase']}' → '{result['recognized']}'")
    
    return results


def test_continuous_monitoring():
    """常時監視モードのテスト"""
    print("=" * 50)
    print("常時監視モードテスト")
    print("=" * 50)
    
    print("常時監視モードを開始します...")
    print("以下を順番に試してください：")
    print("1. おはようルクス")
    print("2. おはようございます")
    print("3. ルクス、今日の天気")
    print("4. 'quit'と言って終了")
    print()
    
    def wake_word_callback(text, command):
        print(f"🚨 【ウェイクワード検知】'{text}' -> コマンド: '{command}'")
    
    try:
        monitor = ContinuousSpeechMonitor(
            wake_word_callback=wake_word_callback,
            use_phonetic_verification=True
        )
        
        monitor.start_monitoring()
        
        # 手動停止待機
        print("監視中... 'quit'と言うか、Ctrl+Cで終了してください")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n監視を停止します...")
        if 'monitor' in locals():
            monitor.stop_monitoring()
    except Exception as e:
        print(f"監視エラー: {e}")


def main():
    """メインテスト関数"""
    print("🎤 ルクス認識精度改善テスト")
    print("問題: 「おはようルクス」→「おはようございます」誤認識対策")
    print()
    
    while True:
        print("テストメニュー:")
        print("1. テキストベース認識テスト")
        print("2. 実際の音声認識テスト")
        print("3. 常時監視モードテスト")
        print("4. 全テスト実行")
        print("0. 終了")
        
        choice = input("\n選択してください (0-4): ").strip()
        
        if choice == "0":
            print("テストを終了します")
            break
        elif choice == "1":
            test_text_based_recognition()
        elif choice == "2":
            test_actual_speech_recognition()
        elif choice == "3":
            test_continuous_monitoring()
        elif choice == "4":
            print("全テストを実行します...\n")
            test_text_based_recognition()
            print("\n" + "="*50 + "\n")
            test_actual_speech_recognition()
        else:
            print("無効な選択です")
        
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()
