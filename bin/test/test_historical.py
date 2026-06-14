import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools import networkx_tools

def test_tool():
    print("Testing Historical Context Extraction...")
    
    # Call core tool directly
    res = networkx_tools.get_historical_investigations_tool("user:Alice")
    
    # Print results
    if res.get('status') == 'success':
        print("\nSuccess!")
        print(f"Patient Zero: {res.get('patient_zero_id')}")
        
        history = res.get('history', [])
        print(f"Historical Investigations Found: {len(history)}")
        for h in history:
            print(f" - [{h.get('time')}] {h.get('alert_id')} | Verdict: {h.get('verdict')} ({h.get('confidence')}%)")
            print(f"   Summary: {h.get('summary')}")
    else:
        print(f"Failed: {res.get('message')}")

if __name__ == '__main__':
    test_tool()
