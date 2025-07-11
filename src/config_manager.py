"""
設定管理モジュール
config.jsonからの設定読み込みとデフォルト値管理
"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 設定ファイル読み込み完了: {self.config_path}")
                return config
            else:
                print(f"⚠️  設定ファイルが見つかりません: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            print("デフォルト設定を使用します")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "audio_input": {
                "sample_rate": 16000,
                "channels": 1,
                "recording_duration": 5,
                "microphone_timeout": 30,
                "phrase_timeout": 5
            },
            "speech_recognition": {
                "language": "ja-JP",
                "alternative_languages": ["en-US"]
            },
            "wake_words": [
                "ルクス", "るくす", "Lux", "lux", "LUX"
            ],
            "exit_commands": [
                "終了", "しゅうりょう", "バイバイ", "ばいばい", "exit", "quit"
            ],
            "audio_output": {
                "rate": 180,
                "volume": 0.8,
                "voice_id": None,
                "max_text_length": 500
            },
            "gemini": {
                "timeout": 30,
                "debug": False,
                "retry_count": 2
            },
            "system": {
                "log_level": "INFO",
                "startup_message": "音声アシスタント ルクス が起動しました。ルクス と呼びかけてください。",
                "shutdown_message": "音声アシスタントを終了します。お疲れ様でした。",
                "ready_message": "はい、何でしょうか？"
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得（ドット記法対応）
        
        Args:
            key_path: 設定キーのパス（例: "audio_input.sample_rate"）
            default: デフォルト値
            
        Returns:
            設定値
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key_path: str, value: Any):
        """
        設定値を変更
        
        Args:
            key_path: 設定キーのパス
            value: 新しい値
        """
        try:
            keys = key_path.split('.')
            config = self._config
            
            # 最後のキー以外まで辿る
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 最後のキーに値を設定
            config[keys[-1]] = value
            
        except Exception as e:
            print(f"設定変更エラー: {e}")
    
    def save_config(self):
        """設定をファイルに保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            print(f"✅ 設定保存完了: {self.config_path}")
        except Exception as e:
            print(f"❌ 設定保存エラー: {e}")
    
    def get_audio_input_config(self) -> Dict[str, Any]:
        """音声入力設定を取得"""
        return self.get("audio_input", {})
    
    def get_speech_recognition_config(self) -> Dict[str, Any]:
        """音声認識設定を取得"""
        return self.get("speech_recognition", {})
    
    def get_audio_output_config(self) -> Dict[str, Any]:
        """音声出力設定を取得"""
        return self.get("audio_output", {})
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """Gemini設定を取得"""
        return self.get("gemini", {})
    
    def get_wake_words(self) -> list:
        """ウェイクワード一覧を取得"""
        return self.get("wake_words", ["ルクス"])
    
    def get_exit_commands(self) -> list:
        """終了コマンド一覧を取得"""
        return self.get("exit_commands", ["終了"])
    
    def get_system_messages(self) -> Dict[str, str]:
        """システムメッセージを取得"""
        return self.get("system", {})
    
    def print_config(self):
        """現在の設定を表示"""
        print("\n=== 現在の設定 ===")
        print(json.dumps(self._config, ensure_ascii=False, indent=2))


def test_config_manager():
    """設定管理のテスト"""
    print("=== 設定管理テスト ===")
    
    config = ConfigManager()
    
    # 設定値取得テスト
    print(f"音声入力サンプルレート: {config.get('audio_input.sample_rate')}")
    print(f"ウェイクワード: {config.get_wake_words()}")
    print(f"音声出力速度: {config.get('audio_output.rate')}")
    
    # 設定変更テスト
    config.set('audio_output.rate', 200)
    print(f"変更後の音声出力速度: {config.get('audio_output.rate')}")
    
    # 全設定表示
    config.print_config()


if __name__ == "__main__":
    test_config_manager()
