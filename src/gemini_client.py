"""
Gemini CLI連携モジュール
音声アシスタント用のGemini CLI通信機能を提供
"""

import subprocess
import json
import logging
from typing import Optional, Dict, Any


class GeminiClient:
    """Gemini CLIとの通信を管理するクラス"""
    
    def __init__(self, 
                 debug: bool = False,
                 timeout: int = 30,
                 model: str = "gemini-2.5-flash"):
        """
        初期化
        
        Args:
            debug: デバッグモード
            timeout: コマンド実行のタイムアウト（秒）
            model: 使用するGeminiモデル
        """
        self.debug = debug
        self.timeout = timeout
        self.model = model
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        print(f"Gemini CLI初期化完了: モデル={self.model}, デバッグ={debug}, タイムアウト={timeout}秒")
        
        # Gemini CLIの動作確認
        self._check_gemini_cli()
    
    def _check_gemini_cli(self) -> bool:
        """Gemini CLIが利用可能かチェック"""
        try:
            # Windows環境では.cmdファイルを直接指定
            result = subprocess.run(
                ['gemini.cmd', '--help'], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='ignore',  # エンコーディングエラーを無視
                timeout=10,
                shell=False
            )
            if result.returncode == 0:
                print(f"✅ Gemini CLI確認: 動作確認完了")
                return True
            else:
                # .cmdが失敗した場合、通常のgeminiを試す
                result2 = subprocess.run(
                    ['gemini', '--help'], 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    errors='ignore',  # エンコーディングエラーを無視
                    timeout=10,
                    shell=True
                )
                if result2.returncode == 0:
                    print(f"✅ Gemini CLI確認: 動作確認完了")
                    return True
                else:
                    print(f"⚠️  Gemini CLI警告: {result.stderr}")
                    return False
                
        except FileNotFoundError:
            print("⚠️  Gemini CLIが見つかりません。")
            print("   以下を確認してください:")
            print("   1. Gemini CLIがインストールされているか")
            print("   2. PATHに追加されているか")
            print("   3. PowerShellで 'gemini --help' が実行できるか")
            self.manual_check_instructions()
            return False
        except subprocess.TimeoutExpired:
            print("⚠️  Gemini CLI応答がタイムアウトしました。")
            return False
        except Exception as e:
            print(f"⚠️  Gemini CLI確認エラー: {e}")
            print("   手動で 'gemini --help' を実行して動作を確認してください")
            return False
    
    def create_assistant_prompt(self, user_input: str) -> str:
        """
        音声アシスタント用のプロンプトを作成（現在はシステムプロンプトなし）
        
        Args:
            user_input: ユーザーからの入力
            
        Returns:
            ユーザー入力をそのまま返す
        """
        # システムプロンプトを無効化 - ユーザー入力をそのまま使用
        return user_input
    
    def send_prompt(self, prompt: str, use_assistant_format: bool = True) -> Optional[str]:
        """
        Gemini CLIにプロンプトを送信し、応答を取得
        
        Args:
            prompt: 送信するプロンプト
            use_assistant_format: 音声アシスタント用フォーマットを使用するか
            
        Returns:
            Geminiからの応答（失敗時はNone）
        """
        try:
            # 音声アシスタント用プロンプトに変換
            if use_assistant_format:
                formatted_prompt = self.create_assistant_prompt(prompt)
            else:
                formatted_prompt = prompt
            
            # コマンドを構築（Windows環境を考慮）
            cmd = ['gemini.cmd', '-m', self.model, '-p', formatted_prompt]
            
            # デバッグモード
            if self.debug:
                cmd.append('-d')
            
            print(f"📤 Geminiに送信中: '{prompt}'")
            if self.debug:
                print(f"デバッグ: コマンド = {' '.join(cmd)}")
            
            # Gemini CLI実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # エンコーディングエラーを無視
                timeout=self.timeout,
                shell=False
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"📥 Gemini応答取得成功")
                return response
            else:
                # .cmdが失敗した場合、通常のgeminiを試す
                cmd_fallback = ['gemini', '-m', self.model, '-p', formatted_prompt]
                if self.debug:
                    cmd_fallback.append('-d')
                
                result_fallback = subprocess.run(
                    cmd_fallback,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',  # エンコーディングエラーを無視
                    timeout=self.timeout,
                    shell=True
                )
                
                if result_fallback.returncode == 0:
                    response = result_fallback.stdout.strip()
                    print(f"📥 Gemini応答取得成功 (fallback)")
                    return response
                else:
                    error_msg = result.stderr.strip() or result_fallback.stderr.strip()
                    print(f"❌ Gemini CLIエラー: {error_msg}")
                    self.logger.error(f"Gemini CLI error: {error_msg}")
                    return None
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Gemini CLI応答がタイムアウトしました（{self.timeout}秒）")
            return None
        except FileNotFoundError:
            print("❌ Gemini CLIが見つかりません")
            print("   PowerShellで 'gemini --help' を実行して確認してください")
            return None
        except Exception as e:
            print(f"❌ Gemini CLI通信エラー: {e}")
            self.logger.error(f"Gemini CLI communication error: {e}")
            return None
    
    def send_command(self, command: str) -> Optional[str]:
        """
        コマンドをGeminiに送信（音声アシスタント用のラッパー）
        
        Args:
            command: ユーザーからのコマンド
            
        Returns:
            Geminiからの応答
        """
        return self.send_prompt(command, use_assistant_format=True)
    
    def send_command_fast(self, command: str) -> Optional[str]:
        """
        高速コマンド送信（音声アシスタント用の最適化版）
        
        Args:
            command: ユーザーからのコマンド
            
        Returns:
            Geminiからの応答
        """
        # 簡単なコマンドかどうかを判定
        simple_commands = [
            '電気', '照明', 'ライト', '温度', '時間', '天気', 
            'つけて', '消して', '教えて', 'どう', 'なに', 'いくつ'
        ]
        
        is_simple = any(word in command for word in simple_commands)
        
        if is_simple:
            # 簡単なコマンドは最適化版を使用
            return self.send_prompt_optimized(command, max_tokens=100)
        else:
            # 複雑なコマンドは通常版を使用
            return self.send_command(command)

    
    def test_connection(self) -> bool:
        """接続テストを実行"""
        print("\n=== Gemini CLI接続テスト ===")
        
        # まずCLI存在確認
        if not self._check_gemini_cli():
            print("❌ Gemini CLIが利用できません")
            return False
        
        test_prompt = "こんにちは"
        response = self.send_prompt(test_prompt, use_assistant_format=True)
        
        if response:
            print(f"✅ 接続テスト成功")
            print(f"テスト応答: {response}")
            return True
        else:
            print("❌ 接続テスト失敗")
            return False
    
    def manual_check_instructions(self):
        """Gemini CLIの手動確認手順を表示"""
        print("\n=== Gemini CLI 手動確認手順 ===")
        print("1. PowerShellまたはコマンドプロンプトを開く")
        print("2. 以下のコマンドを実行:")
        print("   > gemini --help")
        print("3. エラーが出る場合:")
        print("   - Gemini CLIがインストールされているか確認")
        print("   - PATHに追加されているか確認")
        print("   - 'where gemini' でパスを確認")
        print("4. テスト実行:")
        print("   > gemini -p \"こんにちは\"")
        print("="*40)

    def send_prompt_optimized(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """
        最適化されたプロンプト送信（短い応答用）
        
        Args:
            prompt: 送信するプロンプト
            max_tokens: 最大トークン数制限
            
        Returns:
            Geminiからの応答（失敗時はNone）
        """
        try:
            # 短い応答を促すプロンプト修正
            optimized_prompt = f"{prompt}\n（簡潔に答えてください。50文字以内で。）"
            
            # コマンドを構築（タイムアウトを短縮）
            cmd = ['gemini.cmd', '-m', self.model, '-p', optimized_prompt]
            
            if self.debug:
                cmd.append('-d')
                print(f"デバッグ: 最適化コマンド = {' '.join(cmd)}")
            
            print(f"📤 Geminiに最適化送信中: '{prompt}'")
            
            # より短いタイムアウトで実行
            short_timeout = min(self.timeout, 15)  # 最大15秒
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=short_timeout,
                shell=False
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"📥 Gemini最適化応答取得成功")
                return response
            else:
                # フォールバック: 通常の方法を試す
                return self.send_prompt(prompt, use_assistant_format=True)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Gemini最適化応答がタイムアウト（{short_timeout}秒）- 通常方法にフォールバック")
            # タイムアウト時は通常の方法を試す
            return self.send_prompt(prompt, use_assistant_format=True)
        except Exception as e:
            print(f"❌ Gemini最適化通信エラー: {e}")
            # エラー時は通常の方法を試す
            return self.send_prompt(prompt, use_assistant_format=True)
def test_gemini_client():
    """Gemini Client のテスト関数"""
    print("=== Gemini Client テスト ===")
    
    # クライアント初期化
    client = GeminiClient(debug=False)  # デバッグを無効化
    
    # 接続テスト
    if client.test_connection():
        print("\n--- インタラクティブテスト ---")
        print("質問を入力してください（'quit'で終了）:")
        
        try:
            while True:
                user_input = input("\n> ")
                if user_input.lower() in ['quit', 'exit', '終了']:
                    break
                
                if user_input.strip():
                    response = client.send_command(user_input)
                    if response:
                        print(f"Gemini: {response}")
                    else:
                        print("応答を取得できませんでした")
                        
        except KeyboardInterrupt:
            print("\nテストを終了します")
    else:
        print("Gemini CLIとの接続に失敗しました")


if __name__ == "__main__":
    test_gemini_client()
