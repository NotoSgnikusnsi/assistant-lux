"""
ログ管理モジュール
音声アシスタントの動作ログを管理
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(log_level: str = "INFO", 
                  log_file: Optional[str] = None,
                  console_output: bool = True) -> logging.Logger:
    """
    ログシステムを設定
    
    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルパス (Noneの場合はファイル出力なし)
        console_output: コンソール出力するか
        
    Returns:
        設定されたロガー
    """
    # ログレベル設定
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ルートロガー設定
    logger = logging.getLogger("voice_assistant")
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # コンソールハンドラー
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # ファイルハンドラー
    if log_file:
        # ログディレクトリ作成
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def create_session_logger(base_path: str = "logs") -> logging.Logger:
    """
    セッション専用のロガーを作成
    
    Args:
        base_path: ログディレクトリのベースパス
        
    Returns:
        セッション用ロガー
    """
    # セッション用ログファイル名（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(base_path, f"session_{timestamp}.log")
    
    return setup_logging(
        log_level="INFO",
        log_file=log_file,
        console_output=False  # セッションログはファイルのみ
    )


class VoiceAssistantLogger:
    """音声アシスタント専用ログ管理クラス"""
    
    def __init__(self, log_level: str = "INFO", enable_session_log: bool = True):
        """
        初期化
        
        Args:
            log_level: メインログレベル
            enable_session_log: セッションログを有効にするか
        """
        self.main_logger = setup_logging(log_level)
        
        if enable_session_log:
            self.session_logger = create_session_logger()
        else:
            self.session_logger = None
    
    def log_startup(self):
        """起動ログ"""
        msg = "音声アシスタント起動"
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)
    
    def log_wake_word_detected(self, wake_word: str, command: str = ""):
        """ウェイクワード検知ログ"""
        msg = f"ウェイクワード検知: '{wake_word}'"
        if command:
            msg += f", 同時コマンド: '{command}'"
        
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)
    
    def log_command_processing(self, command: str):
        """コマンド処理ログ"""
        msg = f"コマンド処理: '{command}'"
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)
    
    def log_gemini_request(self, prompt: str):
        """Gemini要求ログ"""
        msg = f"Gemini要求: '{prompt[:100]}{'...' if len(prompt) > 100 else ''}'"
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)
    
    def log_gemini_response(self, response: str, success: bool = True):
        """Gemini応答ログ"""
        status = "成功" if success else "失敗"
        msg = f"Gemini応答{status}: '{response[:100] if response else 'なし'}{'...' if response and len(response) > 100 else ''}'"
        
        if success:
            self.main_logger.info(msg)
        else:
            self.main_logger.error(msg)
        
        if self.session_logger:
            if success:
                self.session_logger.info(msg)
            else:
                self.session_logger.error(msg)
    
    def log_audio_output(self, text: str):
        """音声出力ログ"""
        msg = f"音声出力: '{text[:50]}{'...' if len(text) > 50 else ''}'"
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)
    
    def log_error(self, error_msg: str, exception: Exception = None):
        """エラーログ"""
        msg = f"エラー: {error_msg}"
        if exception:
            msg += f" - {str(exception)}"
        
        self.main_logger.error(msg)
        if self.session_logger:
            self.session_logger.error(msg)
    
    def log_shutdown(self):
        """終了ログ"""
        msg = "音声アシスタント終了"
        self.main_logger.info(msg)
        if self.session_logger:
            self.session_logger.info(msg)


def test_logging():
    """ログシステムのテスト"""
    print("=== ログシステムテスト ===")
    
    # ロガー初期化
    va_logger = VoiceAssistantLogger()
    
    # 各種ログテスト
    va_logger.log_startup()
    va_logger.log_wake_word_detected("ルクス", "天気を教えて")
    va_logger.log_command_processing("今日の天気は？")
    va_logger.log_gemini_request("今日の東京の天気を教えて")
    va_logger.log_gemini_response("今日は晴れです", True)
    va_logger.log_audio_output("今日は晴れです")
    va_logger.log_error("テストエラー")
    va_logger.log_shutdown()
    
    print("ログテスト完了")


if __name__ == "__main__":
    test_logging()
