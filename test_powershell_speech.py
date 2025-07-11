"""
PowerShell音声出力テスト
"""

import subprocess

def test_powershell_speech():
    print("=== PowerShell音声出力テスト ===")
    
    test_texts = [
        "こんにちは",
        "音声テストです", 
        "今日の天気は晴れです",
        "音声アシスタント ルクス です"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nテスト {i}: '{text}' を再生...")
        
        try:
            # PowerShellのSystem.Speech.Synthesisを使用
            ps_command = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Volume = 100
$synth.Rate = 0
$synth.Speak('{text}')
"""
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("PowerShell音声再生成功")
            else:
                print(f"PowerShellエラー: {result.stderr}")
                
        except Exception as e:
            print(f"例外エラー: {e}")

if __name__ == "__main__":
    test_powershell_speech()
