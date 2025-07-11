"""
音声出力テスト用スクリプト
"""

from src.audio_output import AudioOutputHandler

def test_gemini_response_audio():
    print("=== Gemini応答音声テスト ===")
    
    # 実際のGemini応答例
    test_response = """MCP STDERR (Home Assistant): [I 2025-07-12 00:57:17,775.775 httpx] HTTP Request: GET http://homeassistant:8123/mcp_server/sse "HTTP/1.1 200 OK"
MCP STDERR (Home Assistant): [I 2025-07-12 00:57:17,782.782 httpx] HTTP Request: POST http://homeassistant:8123/mcp_server/messages/01JZX39252ZX9FZH226WDS2GYF "HTTP/1.1 200 OK"
今日の東京の天気は曇り、気温は22℃です。降水確率は40%です。"""
    
    print("元のGemini応答:")
    print(test_response)
    print("-" * 50)
    
    # 音声出力ハンドラー初期化
    audio_output = AudioOutputHandler()
    
    # ノイズ除去テスト
    cleaned_text = audio_output._clean_text(test_response)
    print("ノイズ除去後:")
    print(f"'{cleaned_text}'")
    print("-" * 50)
    
    # 音声出力テスト
    print("音声出力テスト開始...")
    success = audio_output.speak_text(test_response, blocking=True)
    print(f"音声出力結果: {'成功' if success else '失敗'}")

if __name__ == "__main__":
    test_gemini_response_audio()
