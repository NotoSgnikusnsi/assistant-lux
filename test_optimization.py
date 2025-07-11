"""
最適化機能テストスクリプト
パフォーマンス監視データに基づいた自動最適化をテスト
"""

import sys
from pathlib import Path

# プロジェクトのrootディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.config_manager import ConfigManager
from src.performance_monitor import PerformanceMonitor


def test_optimization():
    """最適化機能をテスト"""
    print("🔧 最適化機能テスト開始")
    print("="*50)
    
    # コンポーネント初期化
    config = ConfigManager("config.json")
    monitor = PerformanceMonitor()
    
    # テストデータを手動で追加（実際の使用をシミュレート）
    print("📊 テストデータを生成中...")
    
    # 遅いGemini通信をシミュレート
    for i in range(5):
        session_id = monitor.start_session(f"テストセッション {i+1}")
        
        # 音声認識（高速）
        step = monitor.start_step("speech_recognition")
        import time
        time.sleep(0.1)  # 100ms
        monitor.finish_step("speech_recognition", True)
        
        # Gemini通信（遅い）
        step = monitor.start_step("gemini_request")
        if i == 0:
            time.sleep(2.0)  # 2000ms (最初は特に遅い)
        elif i < 3:
            time.sleep(1.5)  # 1500ms
        else:
            time.sleep(1.0)  # 1000ms
        monitor.finish_step("gemini_request", True)
        
        # 音声出力（高速）
        step = monitor.start_step("audio_output")
        time.sleep(0.05)  # 50ms
        monitor.finish_step("audio_output", True)
        
        monitor.finish_session(True)
    
    print("✅ テストデータ生成完了\n")
    
    # パフォーマンスレポート表示
    print("📊 現在のパフォーマンス状況:")
    monitor.print_performance_report()
    
    # 最適化推奨表示
    print("\n" + "="*60)
    print("🔍 最適化推奨事項:")
    monitor.print_optimization_guide()
    
    # 最適化適用のテスト
    print("\n" + "="*60)
    print("⚙️ 自動最適化テスト:")
    
    # 現在の設定を表示
    print(f"最適化前のGeminiタイムアウト: {config.get('gemini.timeout')}秒")
    print(f"最適化前のGeminiモデル: {config.get('gemini.model')}")
    print(f"最適化前の録音時間: {config.get('audio_input.recording_duration')}秒")
    
    # 最適化適用
    result = monitor.apply_auto_optimization(config)
    
    if result["status"] == "success":
        print(f"\n✅ 自動最適化成功 (優先度: {result['priority']})")
        print("適用された変更:")
        for change in result["changes"]:
            print(f"   ・{change}")
        
        # 最適化後の設定を表示
        print(f"\n最適化後のGeminiタイムアウト: {config.get('gemini.timeout')}秒")
        print(f"最適化後のGeminiモデル: {config.get('gemini.model')}")
        print(f"最適化後の録音時間: {config.get('audio_input.recording_duration')}秒")
        
    else:
        print(f"❌ 自動最適化失敗: {result.get('message', '不明なエラー')}")
    
    print("\n🏁 最適化機能テスト完了")


def test_optimization_recommendations():
    """最適化推奨機能のテスト"""
    print("\n🎯 最適化推奨機能テスト")
    print("="*40)
    
    monitor = PerformanceMonitor()
    
    # 異なるパフォーマンスシナリオをテスト
    scenarios = [
        {"name": "高速シナリオ", "gemini_time": 0.5, "audio_time": 2.0},
        {"name": "中速シナリオ", "gemini_time": 3.0, "audio_time": 4.0},
        {"name": "低速シナリオ", "gemini_time": 8.0, "audio_time": 6.0},
        {"name": "超低速シナリオ", "gemini_time": 15.0, "audio_time": 8.0},
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}:")
        
        # テストセッション作成
        session_id = monitor.start_session(scenario['name'])
        
        # 音声入力
        step = monitor.start_step("audio_input")
        import time
        time.sleep(scenario['audio_time'] / 10)  # 実際の1/10の時間でシミュレート
        monitor.finish_step("audio_input", True)
        
        # Gemini通信
        step = monitor.start_step("gemini_request")
        time.sleep(scenario['gemini_time'] / 10)  # 実際の1/10の時間でシミュレート
        monitor.finish_step("gemini_request", True)
        
        monitor.finish_session(True)
        
        # 推奨事項を取得
        recommendations = monitor.get_optimization_recommendations()
        
        if "priority" in recommendations:
            priority = recommendations["priority"]
            print(f"   優先度: {priority}")
            
            if recommendations.get("gemini_optimizations"):
                gemini_opts = recommendations["gemini_optimizations"]
                print(f"   Gemini最適化: タイムアウト={gemini_opts.get('timeout', 'N/A')}秒")
            
            if recommendations.get("audio_optimizations"):
                audio_opts = recommendations["audio_optimizations"]
                print(f"   音声最適化: 録音時間={audio_opts.get('recording_duration', 'N/A')}秒")
        
        # 統計をリセット（次のシナリオ用）
        monitor.reset_stats()


if __name__ == "__main__":
    try:
        # 基本最適化テスト
        test_optimization()
        
        # 推奨機能テスト
        test_optimization_recommendations()
        
    except KeyboardInterrupt:
        print("\n👋 テストを中断しました")
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
