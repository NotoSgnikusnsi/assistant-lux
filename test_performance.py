"""
パフォーマンステスト用スクリプト
音声入力からGemini応答出力までの時間を計測してボトルネックを特定
"""

import sys
import os
import time
from pathlib import Path

# プロジェクトのrootディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.audio_input import AudioInputHandler
from src.speech_recognizer import SpeechRecognizer
from src.gemini_client import GeminiClient
from src.audio_output import AudioOutputHandler
from src.config_manager import ConfigManager
from src.performance_monitor import PerformanceMonitor


def test_performance():
    """パフォーマンステストを実行"""
    print("🧪 パフォーマンステスト開始")
    print("="*50)
    
    # 設定読み込み
    config = ConfigManager("config.json")
    
    # パフォーマンス監視初期化
    monitor = PerformanceMonitor()
    
    # コンポーネント初期化
    print("📋 コンポーネント初期化中...")
    
    audio_input_config = config.get_audio_input_config()
    speech_config = config.get_speech_recognition_config()
    audio_output_config = config.get_audio_output_config()
    gemini_config = config.get_gemini_config()
    vad_config = config.get_vad_config()  # VAD設定を取得
    
    audio_handler = AudioInputHandler(
        recording_duration=audio_input_config.get("recording_duration", 5)
    )
    
    speech_recognizer = SpeechRecognizer(
        language=speech_config.get("language", "ja-JP")
    )
    
    gemini_client = GeminiClient(
        debug=gemini_config.get("debug", False),
        timeout=gemini_config.get("timeout", 30),
        model=gemini_config.get("model", "gemini-2.5-flash")
    )
    
    audio_output = AudioOutputHandler(
        rate=audio_output_config.get("rate", 180),
        volume=audio_output_config.get("volume", 0.8),
        voice_id=audio_output_config.get("voice_id"),
        max_text_length=audio_output_config.get("max_text_length", 300)
    )
    
    print("✅ コンポーネント初期化完了")
    print("\n" + "="*50)
    
    # テストシナリオ実行
    test_commands = [
        "今日の天気は？",
        "簡単な計算をして",
        "おはよう",
        "時間を教えて"
    ]
    
    for i, test_command in enumerate(test_commands, 1):
        print(f"\n🧪 テスト {i}/{len(test_commands)}: '{test_command}'")
        run_single_test(monitor, speech_recognizer, gemini_client, audio_output, test_command)
        
        # テスト間の待機
        if i < len(test_commands):
            print("⏳ 3秒間待機...")
            time.sleep(3)
    
    # 最終レポート出力
    print("\n" + "="*60)
    print("🏁 全テスト完了 - 最終パフォーマンスレポート")
    print("="*60)
    monitor.print_performance_report()


def run_single_test(monitor, speech_recognizer, gemini_client, audio_output, test_command):
    """単一テストシナリオを実行"""
    
    # セッション開始
    session_id = monitor.start_session(f"テストコマンド: '{test_command}'")
    
    try:
        # 音声認識シミュレーション（実際の音声入力をスキップ）
        step = monitor.start_step("speech_recognition_simulation")
        print(f"🎤 音声認識シミュレーション: '{test_command}'")
        time.sleep(0.1)  # 音声認識処理時間をシミュレート
        monitor.finish_step("speech_recognition_simulation", True)
        
        # Gemini通信
        step = monitor.start_step("gemini_request")
        print("🤖 Geminiに問い合わせ中...")
        try:
            response = gemini_client.send_command(test_command)
            if response:
                monitor.finish_step("gemini_request", True)
                print(f"💬 Gemini応答: {response[:100]}...")
            else:
                monitor.finish_step("gemini_request", False, "応答なし")
                print("❌ Geminiから応答がありませんでした")
                monitor.finish_session(False)
                return
        except Exception as e:
            monitor.finish_step("gemini_request", False, str(e))
            print(f"❌ Gemini通信エラー: {e}")
            monitor.finish_session(False)
            return
        
        # 音声出力
        step = monitor.start_step("audio_output")
        print("🔊 音声出力中...")
        try:
            # 実際の音声出力（短縮版）
            short_response = response[:100] + "..." if len(response) > 100 else response
            audio_success = audio_output.speak_text(short_response, blocking=True)
            if audio_success:
                monitor.finish_step("audio_output", True)
                print("✅ 音声出力完了")
            else:
                monitor.finish_step("audio_output", False, "音声出力失敗")
                print("❌ 音声出力失敗")
        except Exception as e:
            monitor.finish_step("audio_output", False, str(e))
            print(f"❌ 音声出力エラー: {e}")
        
        # セッション完了
        monitor.finish_session(True)
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        monitor.finish_session(False)


def run_audio_input_test():
    """実際の音声入力テスト"""
    print("\n🎤 実際の音声入力テストを開始しますか？ (y/n)")
    response = input().strip().lower()
    
    if response != 'y':
        print("音声入力テストをスキップします")
        return
    
    print("🎤 音声入力テスト開始")
    config = ConfigManager("config.json")
    monitor = PerformanceMonitor()
    
    audio_input_config = config.get_audio_input_config()
    speech_config = config.get_speech_recognition_config()
    vad_config = config.get_vad_config()  # VAD設定を取得
    
    audio_handler = AudioInputHandler(
        recording_duration=audio_input_config.get("recording_duration", 5)
    )
    
    speech_recognizer = SpeechRecognizer(
        language=speech_config.get("language", "ja-JP")
    )
    
    session_id = monitor.start_session("実音声入力テスト（VAD最適化）")
    
    try:
        # VADを使った音声入力
        step = monitor.start_step("audio_input")
        print("🎤 話してください（発話終了を自動検出します）...")
        audio_data = audio_handler.record_audio_with_vad(
            max_duration=vad_config.get("max_duration", 5),
            silence_threshold=vad_config.get("silence_threshold", 0.005),
            min_duration=vad_config.get("min_duration", 0.3),
            post_silence_duration=vad_config.get("post_silence_duration", 0.8)
        )
        monitor.finish_step("audio_input", True)
        
        if len(audio_data) > 0:
            # 音声認識
            step = monitor.start_step("speech_recognition")
            print("🔍 音声認識中...")
            text = speech_recognizer.recognize_from_audio_data(
                audio_data, 
                audio_handler.sample_rate
            )
            
            if text:
                monitor.finish_step("speech_recognition", True)
                print(f"📝 認識結果: '{text}'")
            else:
                monitor.finish_step("speech_recognition", False, "認識失敗")
                print("❌ 音声を認識できませんでした")
        else:
            print("❌ 音声データがありません")
            monitor.finish_session(False)
            return
        
        monitor.finish_session(True)
        monitor.print_performance_report()
        
    except Exception as e:
        print(f"❌ 音声入力テストエラー: {e}")
        monitor.finish_session(False)


if __name__ == "__main__":
    try:
        # 基本パフォーマンステスト
        test_performance()
        
        # 音声入力テスト（オプション）
        run_audio_input_test()
        
    except KeyboardInterrupt:
        print("\n👋 テストを中断しました")
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
