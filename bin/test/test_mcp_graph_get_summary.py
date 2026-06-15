import os
import sys
import httpx
import json
import base64
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

URL = "https://127.0.0.1:8089/services/mcp"

def get_auth_headers():
    splunk_user = os.environ.get("SPLUNK_USERNAME", "admin")
    splunk_pass = os.environ.get("SPLUNK_PASSWORD", "admin")
    auth_b64 = base64.b64encode(f"{splunk_user}:{splunk_pass}".encode('utf-8')).decode('utf-8')
    return {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }

def call_tool(tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 1,
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    with httpx.Client(verify=False) as client:
        try:
            res = client.post(URL, headers=get_auth_headers(), json=payload, timeout=60.0)
            if res.status_code != 200:
                print(f"❌ Error HTTP {res.status_code}: {res.text}")
                return False
            data = res.json()
            if "error" in data:
                print(f"❌ MCP Error: {data['error']}")
                return False
            print("✅ Success!")
            print(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

def test_main():
    print("Testing SplunkAgent_graph_get_summary...")
    arguments = {
    "action": "get_graph_summary"
}
    assert call_tool("SplunkAgent_graph_get_summary", arguments) == True

if __name__ == "__main__":
    test_main()
