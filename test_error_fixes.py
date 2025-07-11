"""
修正されたエラーハンドリングと最適化機能のテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトのrootディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.gemini_client import GeminiClient
from src.performance_monitor import PerformanceMonitor


def test_gemini_optimization():
    """Gemini最適化機能のテスト"""
    print("🧪 Gemini最適化機能テスト")
    print("="*50)
    
    # Geminiクライアント初期化
    client = GeminiClient(debug=False, timeout=20)
    
    # テストコマンド
    test_commands = [
        "電気をつけて",
        "今日の天気は？",
        "部屋の温度は？",
        "今何時？"
    ]
    
    print("📋 テストケース:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"  {i}. '{cmd}'")
    
    print(f"\n🚀 高速コマンド送信テスト開始...")
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n--- テスト {i}/{len(test_commands)} ---")
        print(f"コマンド: '{command}'")
        
        try:
            import time
            start_time = time.perf_counter()
            
            # 高速コマンド送信を使用
            if hasattr(client, 'send_command_fast'):
                response = client.send_command_fast(command)
                method = "高速送信"
            else:
                response = client.send_command(command)
                method = "通常送信"
            
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # ms
            
            if response:
                print(f"✅ {method}成功 ({duration:.1f}ms)")
                print(f"応答: {response[:100]}...")
                
                # 性能分析
                if duration < 5000:  # 5秒未満
                    print(f"🟢 優秀な応答時間")
                elif duration < 10000:  # 10秒未満
                    print(f"🟡 普通の応答時間")
                else:  # 10秒以上
                    print(f"🔴 遅い応答時間 - 最適化が必要")
            else:
                print(f"❌ {method}失敗 ({duration:.1f}ms)")
                
        except Exception as e:
            print(f"❌ テストエラー: {e}")
        
        # テスト間の待機
        if i < len(test_commands):
            print("⏳ 2秒間待機...")
            time.sleep(2)
    
    print(f"\n🏁 Gemini最適化テスト完了")


def test_performance_monitoring():
    """パフォーマンス監視機能のテスト"""
    print("\n🧪 パフォーマンス監視機能テスト")
    print("="*50)
    
    # パフォーマンス監視初期化
    monitor = PerformanceMonitor()
    
    # テストセッションの実行
    test_scenarios = [
        ("短時間処理", 0.5),
        ("普通の処理", 2.0),
        ("長時間処理", 5.0)
    ]
    
    for scenario_name, duration in test_scenarios:
        print(f"\n--- {scenario_name}シミュレーション ---")
        
        # セッション開始
        session_id = monitor.start_session(scenario_name)
        
        # ステップ実行シミュレーション
        import time
        
        # 音声認識ステップ
        step = monitor.start_step("speech_recognition")
        time.sleep(0.1)  # 音声認識時間シミュレート
        monitor.finish_step("speech_recognition", True)
        
        # Gemini通信ステップ
        step = monitor.start_step("gemini_request")
        time.sleep(duration)  # Gemini応答時間シミュレート
        monitor.finish_step("gemini_request", True)
        
        # 音声出力ステップ
        step = monitor.start_step("audio_output")
        time.sleep(0.3)  # 音声出力時間シミュレート
        monitor.finish_step("audio_output", True)
        
        # セッション完了
        monitor.finish_session(True)
    
    # 統計レポート出力
    print(f"\n📊 パフォーマンスレポート:")
    monitor.print_performance_report()


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n🧪 エラーハンドリングテスト")
    print("="*50)
    
    # 不正なコマンドでのテスト
    client = GeminiClient(debug=False, timeout=5)  # 短いタイムアウト
    
    test_cases = [
        "",  # 空文字列
        "非常に長いコマンドを送信してタイムアウトを発生させる" * 10,  # 長いコマンド
        "正常なコマンド"  # 正常なケース
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- エラーハンドリングテスト {i} ---")
        print(f"入力: '{test_case[:50]}{'...' if len(test_case) > 50 else ''}'")
        
        try:
            response = client.send_command(test_case)
            if response:
                print(f"✅ 正常処理完了")
            else:
                print(f"⚠️ 応答なし（正常なエラーハンドリング）")
        except Exception as e:
            print(f"❌ 例外発生: {e}")


if __name__ == "__main__":
    try:
        # 各テストを実行
        test_gemini_optimization()
        test_performance_monitoring()
        test_error_handling()
        
        print(f"\n🎉 全テスト完了!")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n👋 テストを中断しました")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
