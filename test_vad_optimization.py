"""
VAD最適化テストスクリプト
音声活動検出による性能改善を検証
"""

import time
import numpy as np
from src.config_manager import ConfigManager
from src.audio_input import AudioInputHandler
from src.speech_recognizer import SpeechRecognizer
from src.performance_monitor import PerformanceMonitor


def test_vad_vs_fixed_time():
    """VAD録音と固定時間録音の性能比較"""
    print("=== VAD最適化 vs 固定時間録音 性能比較 ===")
    
    config = ConfigManager()
    vad_config = config.get_vad_config()
    monitor = PerformanceMonitor()
    
    audio_handler = AudioInputHandler()
    speech_recognizer = SpeechRecognizer()
    
    # テスト1: 従来の固定時間録音（10秒）
    print("\n🔴 テスト1: 従来の固定時間録音（10秒）")
    session_id = monitor.start_session("固定時間録音テスト")
    
    try:
        step = monitor.start_step("audio_input_fixed")
        start_time = time.time()
        
        print("🎤 10秒間話してください（固定時間）...")
        audio_data = audio_handler.record_audio(duration=10)
        
        end_time = time.time()
        monitor.finish_step("audio_input_fixed", True)
        
        fixed_time_duration = end_time - start_time
        print(f"⏱️ 固定時間録音: {fixed_time_duration:.2f}秒")
        
        if len(audio_data) > 0:
            step = monitor.start_step("speech_recognition_fixed")
            text = speech_recognizer.recognize_from_audio_data(audio_data, audio_handler.sample_rate)
            monitor.finish_step("speech_recognition_fixed", True)
            print(f"認識結果: {text}")
    
    except Exception as e:
        print(f"固定時間録音エラー: {e}")
        monitor.finish_step("audio_input_fixed", False, str(e))
    
    monitor.finish_session(True)
    
    # 短い休憩
    print("\n⏸️  3秒休憩...")
    time.sleep(3)
    
    # テスト2: VAD最適化録音
    print("\n🟢 テスト2: VAD最適化録音")
    session_id = monitor.start_session("VAD最適化録音テスト")
    
    try:
        step = monitor.start_step("audio_input_vad")
        start_time = time.time()
        
        print("🎤 話してください（発話終了を自動検出）...")
        audio_data = audio_handler.record_audio_with_vad(
            max_duration=vad_config.get("max_duration", 5),
            silence_threshold=vad_config.get("silence_threshold", 0.005),
            min_duration=vad_config.get("min_duration", 0.3),
            post_silence_duration=vad_config.get("post_silence_duration", 0.8)
        )
        
        end_time = time.time()
        monitor.finish_step("audio_input_vad", True)
        
        vad_time_duration = end_time - start_time
        print(f"⏱️ VAD録音: {vad_time_duration:.2f}秒")
        
        if len(audio_data) > 0:
            step = monitor.start_step("speech_recognition_vad")
            text = speech_recognizer.recognize_from_audio_data(audio_data, audio_handler.sample_rate)
            monitor.finish_step("speech_recognition_vad", True)
            print(f"認識結果: {text}")
    
    except Exception as e:
        print(f"VAD録音エラー: {e}")
        monitor.finish_step("audio_input_vad", False, str(e))
    
    monitor.finish_session(True)
    
    # 結果比較
    print(f"\n📊 性能比較結果:")
    print(f"   固定時間録音: {fixed_time_duration:.2f}秒")
    print(f"   VAD最適化録音: {vad_time_duration:.2f}秒")
    
    if vad_time_duration < fixed_time_duration:
        improvement = ((fixed_time_duration - vad_time_duration) / fixed_time_duration) * 100
        print(f"   ✅ VAD最適化により {improvement:.1f}% 高速化")
    else:
        print(f"   ⚠️ この例では固定時間録音の方が短時間でした")
    
    # パフォーマンス統計表示
    print("\n📈 詳細パフォーマンス統計:")
    try:
        monitor.print_performance_report()
    except AttributeError:
        # フォールバック：基本統計を表示
        print("   詳細統計機能は利用できません")
        print(f"   音声入力の最適化: {improvement:.1f}% 高速化を達成")


def test_vad_parameters():
    """VADパラメータの調整テスト"""
    print("\n=== VADパラメータ調整テスト ===")
    
    audio_handler = AudioInputHandler()
    
    # 異なるパラメータでテスト
    test_configs = [
        {
            "name": "高感度設定",
            "max_duration": 3,
            "silence_threshold": 0.003,
            "min_duration": 0.2,
            "post_silence_duration": 0.5
        },
        {
            "name": "標準設定",
            "max_duration": 5,
            "silence_threshold": 0.005,
            "min_duration": 0.3,
            "post_silence_duration": 0.8
        },
        {
            "name": "低感度設定",
            "max_duration": 8,
            "silence_threshold": 0.01,
            "min_duration": 0.5,
            "post_silence_duration": 1.2
        }
    ]
    
    for i, test_config in enumerate(test_configs, 1):
        print(f"\n🔧 テスト{i}: {test_config['name']}")
        print(f"   パラメータ: {test_config}")
        
        try:
            start_time = time.time()
            print("🎤 話してください...")
            
            audio_data = audio_handler.record_audio_with_vad(
                max_duration=test_config["max_duration"],
                silence_threshold=test_config["silence_threshold"],
                min_duration=test_config["min_duration"],
                post_silence_duration=test_config["post_silence_duration"]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            audio_length = len(audio_data) / audio_handler.sample_rate if len(audio_data) > 0 else 0
            
            print(f"   ⏱️ 録音時間: {duration:.2f}秒")
            print(f"   🎵 音声長: {audio_length:.2f}秒")
            
            # 短い休憩
            if i < len(test_configs):
                print("⏸️  2秒休憩...")
                time.sleep(2)
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")


def main():
    """メインテスト実行"""
    print("🚀 VAD最適化テスト開始")
    print("このテストでは、従来の固定時間録音とVAD最適化録音の性能を比較します。")
    print("テスト中は同じ内容を2回話してください。\n")
    
    try:
        # 基本性能比較
        test_vad_vs_fixed_time()
        
        # パラメータ調整テスト
        print("\n" + "="*50)
        print("続けてパラメータ調整テストを実行しますか？ (y/n)")
        response = input().lower().strip()
        
        if response in ['y', 'yes', 'はい']:
            test_vad_parameters()
        
        print("\n✅ VAD最適化テスト完了")
        print("設定ファイル（config.json）のvad_settingsを調整することで、")
        print("音声検出の感度や応答速度を最適化できます。")
        
    except KeyboardInterrupt:
        print("\n⏹️ テストを中断しました")
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")


if __name__ == "__main__":
    main()
