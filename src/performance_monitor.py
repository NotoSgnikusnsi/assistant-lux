"""
パフォーマンス監視モジュール
音声入力からGemini応答出力までの各ステップの実行時間を計測
"""

import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ProcessingStep:
    """処理ステップの実行時間記録"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def finish(self, success: bool = True, error_message: Optional[str] = None):
        """ステップ完了を記録"""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message


@dataclass
class ProcessingSession:
    """1回の音声処理セッションの記録"""
    session_id: str
    start_time: float
    steps: Dict[str, ProcessingStep] = field(default_factory=dict)
    total_duration: Optional[float] = None
    success: bool = True
    
    def add_step(self, step_name: str) -> ProcessingStep:
        """新しい処理ステップを開始"""
        step = ProcessingStep(step_name, time.perf_counter())
        self.steps[step_name] = step
        return step
    
    def finish_session(self, success: bool = True):
        """セッション完了を記録"""
        end_time = time.perf_counter()
        self.total_duration = end_time - self.start_time
        self.success = success


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.sessions: List[ProcessingSession] = []
        self.current_session: Optional[ProcessingSession] = None
        self.step_stats: Dict[str, List[float]] = defaultdict(list)
        self.session_count = 0
    
    def start_session(self, context: str = "") -> str:
        """新しい処理セッションを開始"""
        self.session_count += 1
        session_id = f"session_{self.session_count:04d}"
        
        self.current_session = ProcessingSession(
            session_id=session_id,
            start_time=time.perf_counter()
        )
        
        print(f"📊 セッション開始: {session_id} {context}")
        return session_id
    
    def start_step(self, step_name: str) -> ProcessingStep:
        """処理ステップを開始"""
        if not self.current_session:
            raise RuntimeError("セッションが開始されていません")
        
        step = self.current_session.add_step(step_name)
        print(f"⏱️ ステップ開始: {step_name}")
        return step
    
    def finish_step(self, step_name: str, success: bool = True, error_message: Optional[str] = None):
        """処理ステップを完了"""
        if not self.current_session or step_name not in self.current_session.steps:
            print(f"⚠️ ステップ '{step_name}' が見つかりません")
            return
        
        step = self.current_session.steps[step_name]
        step.finish(success, error_message)
        
        # 統計データに追加
        if step.duration:
            self.step_stats[step_name].append(step.duration)
        
        status = "✅" if success else "❌"
        duration_ms = (step.duration * 1000) if step.duration else 0
        print(f"{status} ステップ完了: {step_name} ({duration_ms:.1f}ms)")
        
        if error_message:
            print(f"   エラー: {error_message}")
    
    def finish_session(self, success: bool = True):
        """現在のセッションを完了"""
        if not self.current_session:
            return
        
        self.current_session.finish_session(success)
        self.sessions.append(self.current_session)
        
        total_ms = (self.current_session.total_duration * 1000) if self.current_session.total_duration else 0
        status = "✅" if success else "❌"
        print(f"{status} セッション完了: {self.current_session.session_id} (総時間: {total_ms:.1f}ms)")
        
        # 詳細ステップ時間を表示
        if self.current_session.steps:
            print("   ステップ詳細:")
            for step_name, step in self.current_session.steps.items():
                if step.duration:
                    step_ms = step.duration * 1000
                    percentage = (step.duration / self.current_session.total_duration) * 100 if self.current_session.total_duration else 0
                    print(f"     {step_name}: {step_ms:.1f}ms ({percentage:.1f}%)")
        
        self.current_session = None
    
    def get_performance_stats(self) -> Dict:
        """パフォーマンス統計を取得"""
        if not self.sessions:
            return {"message": "統計データがありません"}
        
        stats = {
            "total_sessions": len(self.sessions),
            "successful_sessions": sum(1 for s in self.sessions if s.success),
            "step_statistics": {},
            "session_statistics": {}
        }
        
        # セッション統計
        session_durations = [s.total_duration for s in self.sessions if s.total_duration]
        if session_durations:
            stats["session_statistics"] = {
                "average_total_time": statistics.mean(session_durations),
                "median_total_time": statistics.median(session_durations),
                "min_total_time": min(session_durations),
                "max_total_time": max(session_durations),
                "std_dev": statistics.stdev(session_durations) if len(session_durations) > 1 else 0
            }
        
        # ステップ統計
        for step_name, durations in self.step_stats.items():
            if durations:
                stats["step_statistics"][step_name] = {
                    "count": len(durations),
                    "average_time": statistics.mean(durations),
                    "median_time": statistics.median(durations),
                    "min_time": min(durations),
                    "max_time": max(durations),
                    "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0
                }
        
        return stats
    
    def print_performance_report(self):
        """パフォーマンスレポートを出力"""
        stats = self.get_performance_stats()
        
        if "message" in stats:
            print(f"📊 {stats['message']}")
            return
        
        print("\n" + "="*60)
        print("📊 パフォーマンス分析レポート")
        print("="*60)
        
        # セッション概要
        print(f"\n🎯 セッション概要:")
        print(f"   総セッション数: {stats['total_sessions']}")
        print(f"   成功セッション数: {stats['successful_sessions']}")
        success_rate = (stats['successful_sessions'] / stats['total_sessions']) * 100
        print(f"   成功率: {success_rate:.1f}%")
        
        # セッション時間統計
        if "session_statistics" in stats:
            session_stats = stats["session_statistics"]
            print(f"\n⏱️ 総処理時間統計:")
            print(f"   平均時間: {session_stats['average_total_time']*1000:.1f}ms")
            print(f"   中央値: {session_stats['median_total_time']*1000:.1f}ms")
            print(f"   最短時間: {session_stats['min_total_time']*1000:.1f}ms")
            print(f"   最長時間: {session_stats['max_total_time']*1000:.1f}ms")
            print(f"   標準偏差: {session_stats['std_dev']*1000:.1f}ms")
        
        # ステップ別統計とボトルネック分析
        if "step_statistics" in stats:
            print(f"\n🔍 ステップ別統計とボトルネック分析:")
            step_stats = stats["step_statistics"]
            
            # 平均時間でソート（降順）
            sorted_steps = sorted(
                step_stats.items(),
                key=lambda x: x[1]["average_time"],
                reverse=True
            )
            
            total_avg_time = sum(step[1]["average_time"] for step in sorted_steps)
            
            for i, (step_name, step_data) in enumerate(sorted_steps):
                avg_ms = step_data["average_time"] * 1000
                percentage = (step_data["average_time"] / total_avg_time) * 100 if total_avg_time > 0 else 0
                
                # ボトルネック指標
                bottleneck_indicator = ""
                if i == 0:  # 最も時間がかかるステップ
                    bottleneck_indicator = " 🚨 最大ボトルネック"
                elif percentage > 30:
                    bottleneck_indicator = " ⚠️ 高負荷"
                elif percentage > 15:
                    bottleneck_indicator = " 📊 要注意"
                
                print(f"\n   {step_name}:{bottleneck_indicator}")
                print(f"     実行回数: {step_data['count']}")
                print(f"     平均時間: {avg_ms:.1f}ms ({percentage:.1f}%)")
                print(f"     中央値: {step_data['median_time']*1000:.1f}ms")
                print(f"     最短/最長: {step_data['min_time']*1000:.1f}ms / {step_data['max_time']*1000:.1f}ms")
                if step_data['std_dev'] > 0:
                    print(f"     標準偏差: {step_data['std_dev']*1000:.1f}ms")
        
        # 改善提案
        self._print_optimization_suggestions(stats)
        
        # パフォーマンス改善提案の表示
        print(f"\n💡 パフォーマンス改善提案:")
        suggestions = self.get_performance_improvement_suggestions()
        for suggestion in suggestions:
            if suggestion.startswith("→"):
                print(f"     {suggestion}")
            else:
                print(f"   • {suggestion}")
        
        print("="*60)
    
    def _print_optimization_suggestions(self, stats: Dict):
        """最適化提案を出力"""
        print(f"\n💡 最適化提案:")
        
        if "step_statistics" not in stats:
            print("   統計データが不足しています")
            return
        
        step_stats = stats["step_statistics"]
        sorted_steps = sorted(
            step_stats.items(),
            key=lambda x: x[1]["average_time"],
            reverse=True
        )
        
        if not sorted_steps:
            print("   ステップデータがありません")
            return
        
        # 最も時間のかかるステップに対する提案
        slowest_step, slowest_data = sorted_steps[0]
        slowest_time_ms = slowest_data["average_time"] * 1000
        
        suggestions = []
        
        if "audio_input" in slowest_step.lower():
            suggestions.append("・音声録音時間を短縮する")
            suggestions.append("・音声品質設定を調整する")
            suggestions.append("・音声バッファサイズを最適化する")
        
        elif "speech_recognition" in slowest_step.lower():
            suggestions.append("・並列音声認識を有効にする")
            suggestions.append("・音声認識エンジンを変更する")
            suggestions.append("・音声前処理を最適化する")
        
        elif "gemini" in slowest_step.lower():
            suggestions.append("・Geminiのタイムアウト設定を調整する")
            suggestions.append("・より高速なモデルに変更する")
            suggestions.append("・プロンプトを簡潔にする")
            suggestions.append("・並列処理を検討する")
        
        elif "audio_output" in slowest_step.lower():
            suggestions.append("・音声キャッシュ機能を有効にする")
            suggestions.append("・音声合成速度を上げる")
            suggestions.append("・音声出力を非同期にする")
        
        if suggestions:
            print(f"   {slowest_step} (平均{slowest_time_ms:.1f}ms) に対する提案:")
            for suggestion in suggestions:
                print(f"     {suggestion}")
        
        # 全体的な提案
        total_time = sum(step[1]["average_time"] for step in sorted_steps) * 1000
        if total_time > 3000:  # 3秒以上
            print(f"\n   全体的な改善提案:")
            print(f"     ・処理の並列化を検討してください")
            print(f"     ・キャッシュ機能を活用してください")
            print(f"     ・不要な処理ステップを削除してください")
    
    def get_performance_improvement_suggestions(self) -> List[str]:
        """
        パフォーマンス改善提案を取得
        
        Returns:
            改善提案のリスト
        """
        suggestions = []
        stats = self.get_performance_stats()
        
        if "step_statistics" not in stats:
            return ["統計データが不足しています"]
        
        step_stats = stats["step_statistics"]
        
        # Gemini処理が遅い場合
        if "gemini_request" in step_stats:
            gemini_avg_time = step_stats["gemini_request"]["average_time"]
            if gemini_avg_time > 10:  # 10秒以上
                suggestions.append("Geminiの応答が遅すぎます (>10秒)")
                suggestions.append("→ モデルをgemini-1.5-flashに変更を検討")
                suggestions.append("→ プロンプトを簡潔にしてください")
                suggestions.append("→ タイムアウト設定を短縮してください")
            elif gemini_avg_time > 5:  # 5秒以上
                suggestions.append("Geminiの応答がやや遅いです (>5秒)")
                suggestions.append("→ 簡潔な応答を求めるプロンプトに変更")
        
        # 音声処理が遅い場合
        if "audio_output" in step_stats:
            audio_avg_time = step_stats["audio_output"]["average_time"]
            if audio_avg_time > 3:  # 3秒以上
                suggestions.append("音声出力が遅いです (>3秒)")
                suggestions.append("→ 音声合成速度を上げてください")
                suggestions.append("→ 音声キャッシュを有効にしてください")
        
        # 全体処理時間
        if "session_statistics" in stats:
            total_avg_time = stats["session_statistics"]["average_total_time"]
            if total_avg_time > 15:  # 15秒以上
                suggestions.append("全体処理時間が長すぎます (>15秒)")
                suggestions.append("→ 並列処理の有効化を検討")
                suggestions.append("→ 不要な処理ステップの削除")
        
        if not suggestions:
            suggestions.append("現在のパフォーマンスは良好です！")
        
        return suggestions
    
    def reset_stats(self):
        """統計データをリセット"""
        self.sessions.clear()
        self.step_stats.clear()
        self.current_session = None
        self.session_count = 0
        print("📊 パフォーマンス統計をリセットしました")
