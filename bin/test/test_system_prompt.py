import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools import tools

def test_system_prompt():
    print("Testing System Prompt Tool Extraction...")
    res = tools.get_system_prompt_tool()
    
    if res.get('status') == 'success':
        print("\n✅ Success!")
        print(f"System Prompt Length: {len(res.get('system_prompt', ''))} characters")
        print("--- PROMPT SNIPPET ---")
        print(res.get('system_prompt', '')[:300] + "...\n[TRUNCATED]")
    else:
        print(f"❌ Failed: {res.get('message')}")

if __name__ == '__main__':
    test_system_prompt()
