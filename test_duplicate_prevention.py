"""
重複処理防止機能のテストスクリプト
"""

import sys
import time
from pathlib import Path

# プロジェクトのrootディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.continuous_speech import ContinuousSpeechMonitor


def test_duplicate_prevention():
    """重複処理防止機能のテスト"""
    print("🧪 重複処理防止機能テスト開始")
    print("="*50)
    
    # テスト用のコールバック
    detection_count = {'count': 0}
    
    def on_wake_word(detected_text: str, extracted_command: str):
        detection_count['count'] += 1
        current_time = time.strftime("%H:%M:%S")
        print(f"[{current_time}] 検知#{detection_count['count']}: '{detected_text}' → '{extracted_command}'")
    
    # 常時音声監視初期化
    monitor = ContinuousSpeechMonitor()
    monitor.set_wake_word_callback(on_wake_word)
    
    # 重複防止設定をテスト用に短縮
    monitor.wake_word_cooldown = 1.0  # 1秒
    monitor.audio_output_suppression_time = 1.0  # 1秒
    
    print(f"⚙️ 設定:")
    print(f"   ウェイクワードクールダウン: {monitor.wake_word_cooldown}秒")
    print(f"   音声出力後抑制時間: {monitor.audio_output_suppression_time}秒")
    print(f"   音韻的検証: {'有効' if monitor.use_phonetic_verification else '無効'}")
    
    print("\n📋 テストシナリオ:")
    print("1. 同じ音声を短時間に複数回認識させる")
    print("2. 音声出力後の検知抑制をテストする")
    print("3. 統計情報を確認する")
    
    # テスト実行フラグ
    test_running = True
    
    def show_instructions():
        print("\n" + "="*50)
        print("🎤 テスト実行中...")
        print("操作方法:")
        print("  's' キー: 統計表示")
        print("  'o' キー: 音声出力シミュレート")
        print("  'r' キー: 統計リセット")
        print("  'q' キー: テスト終了")
        print("="*50)
    
    try:
        monitor.start_monitoring()
        show_instructions()
        
        import sys
        if sys.platform == "win32":
            import msvcrt
            
            while test_running:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    
                    if key == 's':
                        # 統計表示
                        stats = monitor.get_detection_statistics()
                        print(f"\n📊 検知統計:")
                        print(f"   総検知: {stats['total_detections']}")
                        print(f"   基本検知: {stats['basic_detections']}")
                        print(f"   音韻検証成功: {stats['phonetic_verified']}")
                        print(f"   音韻検証却下: {stats['phonetic_rejected']}")
                        print(f"   コールバック実行: {detection_count['count']}")
                        
                    elif key == 'o':
                        # 音声出力シミュレート
                        print("🔊 音声出力シミュレート開始...")
                        monitor.set_audio_output_active(True)
                        time.sleep(0.5)  # 音声出力時間をシミュレート
                        monitor.set_audio_output_active(False)
                        print("🔊 音声出力シミュレート完了")
                        
                    elif key == 'r':
                        # 統計リセット
                        monitor.detection_stats = {
                            'total_detections': 0,
                            'phonetic_verified': 0,
                            'phonetic_rejected': 0,
                            'basic_detections': 0
                        }
                        detection_count['count'] = 0
                        print("📊 統計をリセットしました")
                        
                    elif key == 'q':
                        test_running = False
                        break
                        
                time.sleep(0.1)
        else:
            print("Windowsでのみ対話的テストが可能です")
            print("10秒後に自動終了します...")
            time.sleep(10)
            test_running = False
            
    except KeyboardInterrupt:
        print("\n👋 テストを中断しました")
    finally:
        monitor.cleanup()
        
        # 最終統計表示
        print("\n" + "="*50)
        print("🏁 テスト完了 - 最終統計")
        print("="*50)
        
        stats = monitor.get_detection_statistics()
        print(f"総検知: {stats['total_detections']}")
        print(f"基本検知: {stats['basic_detections']}")
        print(f"音韻検証成功: {stats['phonetic_verified']}")
        print(f"音韻検証却下: {stats['phonetic_rejected']}")
        print(f"コールバック実行: {detection_count['count']}")
        
        if stats['total_detections'] > 0:
            success_rate = (stats['phonetic_verified'] / stats['total_detections']) * 100
            callback_rate = (detection_count['count'] / stats['total_detections']) * 100
            print(f"\n成功率: {success_rate:.1f}%")
            print(f"コールバック実行率: {callback_rate:.1f}%")
            
            if callback_rate < success_rate:
                prevented = stats['phonetic_verified'] - detection_count['count']
                print(f"重複防止により {prevented} 回の処理を回避しました")


if __name__ == "__main__":
    test_duplicate_prevention()
