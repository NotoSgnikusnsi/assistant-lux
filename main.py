"""
音声アシスタント メインアプリケーション
常時ウェイクワード検知と音声入力機能
"""

import time
import signal
import sys
import threading
from src.audio_input import AudioInputHandler
from src.speech_recognizer import SpeechRecognizer
from src.continuous_speech import ContinuousSpeechMonitor
from src.gemini_client import GeminiClient
from src.audio_output import AudioOutputHandler
from src.config_manager import ConfigManager
from src.logger import VoiceAssistantLogger
from src.performance_monitor import PerformanceMonitor


class VoiceAssistant:
    """音声アシスタントのメインクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """初期化"""
        print("=== 音声アシスタント起動中 ===")
        
        # 設定管理初期化
        self.config = ConfigManager(config_path)
        
        # ログシステム初期化
        log_level = self.config.get("system.log_level", "INFO")
        self.logger = VoiceAssistantLogger(log_level=log_level, enable_session_log=True)
        
        # パフォーマンス監視システム初期化
        self.performance_monitor = PerformanceMonitor()
        print("📊 パフォーマンス監視システム有効")
        
        # 設定値取得
        audio_input_config = self.config.get_audio_input_config()
        speech_config = self.config.get_speech_recognition_config()
        audio_output_config = self.config.get_audio_output_config()
        gemini_config = self.config.get_gemini_config()
        
        # 音声最適化設定取得
        optimization_config = self.config.get("audio_optimization", {})
        
        # 重複処理防止設定
        duplicate_prevention = optimization_config.get("duplicate_prevention", {})
        self.command_cooldown = duplicate_prevention.get("command_cooldown", 2.0)
        self.wake_word_cooldown = duplicate_prevention.get("wake_word_cooldown", 3.0)
        self.audio_output_suppression_time = duplicate_prevention.get("audio_output_suppression_time", 2.0)
        
        # 音声最適化システム初期化
        if optimization_config.get("dynamic_quality", False):
            from src.dynamic_audio import DynamicAudioOptimizer, AudioProcessingMonitor
            quality_profiles = optimization_config.get("quality_profiles", {})
            self.audio_optimizer = DynamicAudioOptimizer(quality_profiles)
            self.audio_processing_monitor = AudioProcessingMonitor(self.audio_optimizer)
            self.audio_processing_monitor.start_monitoring()
            print("🎛️ 動的音声品質調整システム有効")
        else:
            self.audio_optimizer = None
            self.audio_processing_monitor = None
        
        # 並列音声認識システム初期化
        if optimization_config.get("parallel_recognition", False):
            from src.parallel_speech import ParallelSpeechRecognizer
            self.parallel_speech = ParallelSpeechRecognizer(
                language=speech_config.get("language", "ja-JP")
            )
            print("🎙️ 並列音声認識システム有効")
        else:
            self.parallel_speech = None
        
        # コンポーネント初期化
        # VAD設定を取得
        vad_config = self.config.get_vad_config()
        
        self.audio_handler = AudioInputHandler(
            recording_duration=audio_input_config.get("recording_duration", 5)
        )
        
        # VAD設定をパフォーマンス向上のため保存
        self.vad_max_duration = vad_config.get("max_duration", 5)
        self.vad_silence_threshold = vad_config.get("silence_threshold", 0.005)
        self.vad_min_duration = vad_config.get("min_duration", 0.3)
        self.vad_post_silence_duration = vad_config.get("post_silence_duration", 0.8)
        
        self.speech_recognizer = SpeechRecognizer(
            language=speech_config.get("language", "ja-JP")
        )
        self.gemini_client = GeminiClient(
            debug=gemini_config.get("debug", False),
            timeout=gemini_config.get("timeout", 30),
            optimized_timeout=gemini_config.get("optimized_timeout", 15),
            enable_optimization=gemini_config.get("enable_optimization", True),
            model=gemini_config.get("model", "gemini-2.5-flash")
        )
        
        # 音声出力（キャッシュ機能を有効化）
        cache_phrases = optimization_config.get("cache_phrases", []) if optimization_config.get("pregenerated_cache", False) else None
        self.audio_output = AudioOutputHandler(
            rate=audio_output_config.get("rate", 180),
            volume=audio_output_config.get("volume", 0.8),
            voice_id=audio_output_config.get("voice_id"),
            max_text_length=audio_output_config.get("max_text_length", 300),
            cache_phrases=cache_phrases,
            enable_sound_effects=audio_output_config.get("enable_sound_effects", True),
            sound_effect_volume=audio_output_config.get("sound_effect_volume", 0.5)
        )
        
        # 状態管理
        self.is_running = True
        self.wake_words = self.config.get_wake_words()
        self.exit_commands = self.config.get_exit_commands()
        self.performance_commands = self.config.get("performance_commands", [])
        self.optimization_commands = self.config.get("optimization_commands", [])
        self.system_messages = self.config.get_system_messages()
        
        # 常時音声監視システム初期化
        self.continuous_monitor = ContinuousSpeechMonitor(
            language=speech_config.get("language", "ja-JP"),
            wake_words=self.wake_words,
            audio_handler=self.audio_output
        )
        self.continuous_monitor.set_wake_word_callback(self._on_wake_word_detected)
        
        # 重複防止設定を反映
        self.continuous_monitor.wake_word_cooldown = self.wake_word_cooldown
        self.continuous_monitor.audio_output_suppression_time = self.audio_output_suppression_time
        
        # 処理状態管理
        self.is_processing_command = False
        self.command_lock = threading.Lock()
        self.last_processed_command = ""
        self.last_command_time = 0
        
        self.logger.log_startup()
        print("初期化完了！")
    
    def _on_wake_word_detected(self, detected_text: str, extracted_command: str):
        """
        ウェイクワード検知時のコールバック
        
        Args:
            detected_text: 検知されたテキスト
            extracted_command: 抽出されたコマンド
        """
        with self.command_lock:
            if self.is_processing_command:
                print("🔄 処理中のため、ウェイクワードを無視します")
                return
            
            # 重複コマンド検知防止
            current_time = time.time()
            if (extracted_command == self.last_processed_command and 
                current_time - self.last_command_time < self.command_cooldown):
                print(f"🔄 同じコマンドのクールダウン中 ({self.command_cooldown}秒): '{extracted_command}'")
                return
            
            self.is_processing_command = True
            self.last_processed_command = extracted_command
            self.last_command_time = current_time
        
        try:
            # パフォーマンス測定開始
            session_id = self.performance_monitor.start_session(f"ウェイクワード: '{detected_text}'")
            
            print(f"🎤 ウェイクワード検知: '{detected_text}'")
            self.logger.log_wake_word_detected(detected_text, extracted_command)
            
            if extracted_command.strip():
                # コマンドが同時に検知された場合
                print(f"同時に検知されたコマンド: '{extracted_command}'")
                self.process_command(extracted_command)
            else:
                # コマンドが検知されていない場合、追加入力を待つ
                ready_msg = self.system_messages.get("ready_message", "はい、何でしょうか？")
                
                # 音声出力ステップ計測
                step = self.performance_monitor.start_step("ready_message_output")
                try:
                    # 音声出力中は音声検知を停止
                    self.continuous_monitor.set_audio_output_active(True)
                    self.audio_output.speak_text(ready_msg, blocking=False)
                    self.performance_monitor.finish_step("ready_message_output", True)
                except Exception as e:
                    self.performance_monitor.finish_step("ready_message_output", False, str(e))
                    raise
                finally:
                    # 音声出力完了後は音声検知を再開
                    time.sleep(0.3)  # 短めの待機時間
                    self.continuous_monitor.set_audio_output_active(False)
                
                # 追加コマンド入力待機（非ブロッキング）
                threading.Thread(target=self._wait_for_additional_command, daemon=True).start()
        
        except Exception as e:
            import traceback
            print(f"ウェイクワード処理エラー: {e}")
            print(f"詳細エラー情報: {traceback.format_exc()}")
            self.performance_monitor.finish_session(False)
        finally:
            with self.command_lock:
                self.is_processing_command = False
    
    def _wait_for_additional_command(self):
        """
        ウェイクワード検知後の追加コマンド待機
        """
        try:
            print("\n--- 追加コマンド入力待機 ---")
            print("ご用件をお話しください（10秒以内）...")
            
            # 音声入力ステップ計測（VAD使用）
            step = self.performance_monitor.start_step("audio_input")
            try:
                # VADを使用したスマート録音（設定ファイルからパラメータを取得）
                audio_data = self.audio_handler.record_audio_with_vad(
                    max_duration=self.vad_max_duration,
                    silence_threshold=self.vad_silence_threshold,
                    min_duration=self.vad_min_duration,
                    post_silence_duration=self.vad_post_silence_duration
                )
                self.performance_monitor.finish_step("audio_input", True)
            except Exception as e:
                self.performance_monitor.finish_step("audio_input", False, str(e))
                raise
            
            if len(audio_data) > 0:
                # 音声認識ステップ計測
                step = self.performance_monitor.start_step("speech_recognition")
                try:
                    text = self.speech_recognizer.recognize_from_audio_data(
                        audio_data, 
                        self.audio_handler.sample_rate
                    )
                    self.performance_monitor.finish_step("speech_recognition", True)
                except Exception as e:
                    self.performance_monitor.finish_step("speech_recognition", False, str(e))
                    raise
                
                if text:
                    print(f"📝 認識されたコマンド: '{text}'")
                    self.process_command(text)
                else:
                    print("音声を認識できませんでした")
                    self.performance_monitor.finish_session(False)
            else:
                print("音声データがありません")
                self.performance_monitor.finish_session(False)
        
        except Exception as e:
            print(f"追加コマンド入力エラー: {e}")
            self.performance_monitor.finish_session(False)
        finally:
            with self.command_lock:
                self.is_processing_command = False
    
    # 旧来の音声入力メソッド（常時監視により不要）
    # def listen_for_command(self, initial_command: str = "") -> str:
    
    def process_command(self, command: str):
        """
        コマンドを処理し、Gemini CLIに送信して応答を取得
        
        Args:
            command: 認識されたコマンド
        """
        print(f"\n=== コマンド処理 ===")
        print(f"📝 入力内容: {command}")
        self.logger.log_command_processing(command)
        
        # セッションが開始されていない場合は新規開始
        if not self.performance_monitor.current_session:
            self.performance_monitor.start_session(f"直接コマンド: '{command}'")
        
        # 終了コマンドのチェック
        if any(word in command.lower() for word in self.exit_commands):
            print("👋 音声アシスタントを終了します")
            
            # 終了メッセージ出力ステップ計測
            step = self.performance_monitor.start_step("shutdown_message_output")
            try:
                shutdown_msg = self.system_messages.get("shutdown_message", "音声アシスタントを終了します。お疲れ様でした。")
                self.audio_output.speak_text(shutdown_msg, blocking=True)
                self.performance_monitor.finish_step("shutdown_message_output", True)
            except Exception as e:
                self.performance_monitor.finish_step("shutdown_message_output", False, str(e))
            
            self.logger.log_shutdown()
            self.performance_monitor.finish_session(True)
            self.is_running = False
            return

        # パフォーマンス統計表示コマンドのチェック
        if any(word in command.lower() for word in self.performance_commands):
            print("📊 パフォーマンス統計を表示します")
            self.performance_monitor.print_performance_report()
            
            # 最適化ガイドも表示
            self.performance_monitor.print_optimization_guide()
            
            # 統計音声出力ステップ計測
            step = self.performance_monitor.start_step("stats_audio_output")
            try:
                stats_msg = "パフォーマンス統計を表示しました。詳細はコンソールをご確認ください。"
                self.audio_output.speak_text(stats_msg, blocking=True)
                self.performance_monitor.finish_step("stats_audio_output", True)
            except Exception as e:
                self.performance_monitor.finish_step("stats_audio_output", False, str(e))
            
            self.performance_monitor.finish_session(True)
            return

        # 最適化コマンドのチェック
        if any(word in command.lower() for word in self.optimization_commands):
            print("⚙️ システム最適化を実行します")
            
            # 最適化ステップ計測
            step = self.performance_monitor.start_step("auto_optimization")
            try:
                result = self.performance_monitor.apply_auto_optimization(self.config)
                
                if result["status"] == "success":
                    self.performance_monitor.finish_step("auto_optimization", True)
                    print(f"✅ 最適化完了 (優先度: {result['priority']})")
                    print("適用された変更:")
                    for change in result["changes"]:
                        print(f"   ・{change}")
                    
                    # 最適化音声出力
                    step = self.performance_monitor.start_step("optimization_audio_output")
                    try:
                        opt_msg = f"システム最適化を完了しました。{len(result['changes'])}項目の設定を更新しました。"
                        self.audio_output.speak_text(opt_msg, blocking=True)
                        self.performance_monitor.finish_step("optimization_audio_output", True)
                    except Exception as e:
                        self.performance_monitor.finish_step("optimization_audio_output", False, str(e))
                    
                    print("\n🔄 設定を反映するにはアプリケーションを再起動してください")
                    
                else:
                    self.performance_monitor.finish_step("auto_optimization", False, result.get("message", "不明なエラー"))
                    print(f"❌ 最適化失敗: {result.get('message', '不明なエラー')}")
                    
                    # エラー音声出力
                    step = self.performance_monitor.start_step("optimization_error_audio_output")
                    try:
                        error_msg = "最適化に失敗しました。詳細はコンソールをご確認ください。"
                        self.audio_output.speak_text(error_msg, blocking=True)
                        self.performance_monitor.finish_step("optimization_error_audio_output", True)
                    except Exception as e:
                        self.performance_monitor.finish_step("optimization_error_audio_output", False, str(e))
                
            except Exception as e:
                self.performance_monitor.finish_step("auto_optimization", False, str(e))
                print(f"❌ 最適化実行エラー: {e}")
            
            self.performance_monitor.finish_session(True)
            return

        # Gemini通信ステップ計測
        step = self.performance_monitor.start_step("gemini_request")
        print("🤖 Geminiに問い合わせ中...")
        self.logger.log_gemini_request(command)
        
        try:
            # 高速コマンド送信を使用
            response = self.gemini_client.send_command_fast(command)
            self.performance_monitor.finish_step("gemini_request", True)
            
            if response:
                self.logger.log_gemini_response(response, True)
                print(f"\n💬 【Gemini応答】")
                print(f"{response}")
                print(f"{'='*50}")
                
                # 音声出力ステップ計測
                step = self.performance_monitor.start_step("audio_output")
                print("🔊 音声で応答を再生中...")
                print(f"DEBUG: 応答テキスト長: {len(response)}")
                print(f"DEBUG: 応答の最初の100文字: {response[:100]}")
                
                self.logger.log_audio_output(response)
                
                try:
                    # 音声出力中は音声検知を停止
                    self.continuous_monitor.set_audio_output_active(True)
                    
                    # 音声出力前の追加チェック
                    if self.audio_output and self.audio_output.engine:
                        print("DEBUG: 音声エンジン確認OK")
                        audio_success = self.audio_output.speak_text(response, blocking=False)  # 非同期に変更
                        print(f"DEBUG: 音声出力結果: {audio_success}")
                        if audio_success:
                            print("✅ 音声再生開始")
                            self.performance_monitor.finish_step("audio_output", True)
                        else:
                            print("❌ 音声再生失敗")
                            self.performance_monitor.finish_step("audio_output", False, "音声再生失敗")
                    else:
                        print("❌ 音声エンジンが利用できません")
                        print("DEBUG: audio_output存在:", self.audio_output is not None)
                        if self.audio_output:
                            print("DEBUG: engine存在:", self.audio_output.engine is not None)
                        self.performance_monitor.finish_step("audio_output", False, "音声エンジン利用不可")
                except Exception as e:
                    self.performance_monitor.finish_step("audio_output", False, str(e))
                    raise
                finally:
                    # 音声出力完了後は音声検知を再開（短い待機時間）
                    time.sleep(0.2)  # 200msに短縮
                    self.continuous_monitor.set_audio_output_active(False)
                
                # セッション成功完了
                self.performance_monitor.finish_session(True)
                
            else:
                error_msg = "Geminiからの応答を取得できませんでした"
                self.logger.log_gemini_response("", False)
                print(f"❌ {error_msg}")
                
                # エラー音声出力
                step = self.performance_monitor.start_step("error_audio_output")
                try:
                    self.continuous_monitor.set_audio_output_active(True)
                    self.audio_output.speak_text(error_msg, blocking=True)
                    self.performance_monitor.finish_step("error_audio_output", True)
                except Exception as e:
                    self.performance_monitor.finish_step("error_audio_output", False, str(e))
                finally:
                    time.sleep(0.5)
                    self.continuous_monitor.set_audio_output_active(False)
                
                self.performance_monitor.finish_session(False)
                
        except Exception as e:
            error_msg = f"Gemini通信エラーが発生しました: {str(e)}"
            self.performance_monitor.finish_step("gemini_request", False, str(e))
            self.logger.log_error("Gemini通信エラー", e)
            print(f"❌ {error_msg}")
            print("接続状況を確認してください")
            
            # エラー音声出力
            step = self.performance_monitor.start_step("error_audio_output")
            try:
                self.continuous_monitor.set_audio_output_active(True)
                self.audio_output.speak_text("通信エラーが発生しました", blocking=True)
                self.performance_monitor.finish_step("error_audio_output", True)
            except Exception as e2:
                self.performance_monitor.finish_step("error_audio_output", False, str(e2))
            finally:
                time.sleep(0.5)
                self.continuous_monitor.set_audio_output_active(False)
            
            self.performance_monitor.finish_session(False)
    
    def run(self):
        """メインループ実行"""
        print("\n🎤 音声アシスタントが開始されました")
        print("Ctrl+C で終了できます")
        
        try:
            # 常時音声監視開始（起動案内前に開始）
            self.continuous_monitor.start_monitoring()
            print("📡 常時ウェイクワード監視開始")
            print(f"ウェイクワード: {', '.join(self.wake_words)}")
            print("いつでもウェイクワードを話しかけてください...")
            
            # 音声出力状態を通知（起動案内中は音声検知を抑制）
            self.continuous_monitor.set_audio_output_active(True)
            
            # 起動音声案内（音声検知開始後に実行）
            startup_msg = self.system_messages.get("startup_message", "音声アシスタント ルクス が起動しました。ルクス と呼びかけてください。")
            self.audio_output.speak_text(startup_msg, blocking=True)
            
            # 音声出力完了後、音声検知を再開
            self.continuous_monitor.set_audio_output_active(False)
            
            # メインループ - 常時監視状態を維持
            while self.is_running:
                time.sleep(0.5)  # CPU使用率を下げるため
                
        except KeyboardInterrupt:
            print("\n\n👋 音声アシスタントを終了します")
        except Exception as e:
            print(f"\n予期せぬエラー: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """リソースの清理と統計情報表示"""
        try:
            print("\n📊 === パフォーマンス統計 ===")
            
            # パフォーマンスレポート出力
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.print_performance_report()
            
            # 常時監視システム停止
            if hasattr(self, 'continuous_monitor'):
                self.continuous_monitor.cleanup()
            
            # 音声出力統計
            if hasattr(self.audio_output, 'get_stats'):
                audio_stats = self.audio_output.get_stats()
                print(f"🔊 音声出力統計:")
                print(f"   総出力回数: {audio_stats.get('total_outputs', 0)}")
                print(f"   キャッシュヒット率: {audio_stats.get('cache_hit_rate', 0):.1%}")
                print(f"   平均処理時間: {audio_stats.get('average_processing_time', 0):.2f}秒")
            
            # 並列音声認識統計
            if self.parallel_speech:
                speech_stats = self.parallel_speech.get_stats()
                print(f"🎙️ 音声認識統計:")
                print(f"   認識成功率: {speech_stats.get('success_rate', 0):.1%}")
                print(f"   平均処理時間: {speech_stats.get('average_processing_time', 0):.2f}秒")
                print(f"   並列実行回数: {speech_stats.get('parallel_recognitions', 0)}")
            
            # 動的音声品質統計
            if self.audio_optimizer:
                optimizer_stats = self.audio_optimizer.get_performance_stats()
                print(f"🎛️ 音声品質統計:")
                print(f"   プロファイル切替回数: {optimizer_stats.get('profile_switches', 0)}")
                print(f"   現在のプロファイル: {optimizer_stats.get('current_profile', 'なし')}")
            
            # システム終了処理
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                # パフォーマンス監視にはstop_monitoringメソッドはないのでコメントアウト
                pass
            
            if self.parallel_speech:
                self.parallel_speech.shutdown()
            
            if self.audio_optimizer:
                self.audio_optimizer.cleanup()
            
            if hasattr(self.audio_output, 'cleanup'):
                self.audio_output.cleanup()
            
            # 終了メッセージ
            shutdown_msg = self.system_messages.get("shutdown_message", "音声アシスタントを終了します。お疲れ様でした。")
            print(f"\n{shutdown_msg}")
            
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")


def signal_handler(signum, frame):
    """シグナルハンドラー（Ctrl+C対応）"""
    print("\n\n終了シグナルを受信しました...")
    sys.exit(0)


def main():
    """メイン関数"""
    # シグナルハンドラー設定
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 音声アシスタント起動
        assistant = VoiceAssistant()
        assistant.run()
        
    except Exception as e:
        print(f"起動エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
