import sys
import json
import urllib.request
import urllib.error
import ssl

# Fix unicode encoding errors for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Connecting to Splunk MCP Server to get graph summary...")
    
    server_uri = "https://127.0.0.1:8089"
    headers = {
        'Authorization': 'Basic c2FteWFrOklpaXRtQDIwMDU=', 
        'Content-Type': 'application/json'
    }
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Payload to call SplunkAgent_graph_get_summary
    payload = {
        "method": "tools/call",
        "params": {
            "name": "SplunkAgent_graph_get_summary",
            "arguments": {
                "action": "get_graph_summary"
            }
        }
    }
    
    req = urllib.request.Request(
        f"{server_uri}/services/mcp",
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            
            if 'error' in res_json:
                print(f"❌ MCP Error: {res_json['error']}")
                sys.exit(1)
                
            tool_result = res_json.get('result', {})
            content = tool_result.get('content', [])
            
            if content and len(content) > 0:
                print("✅ Graph Summary Retrieved successfully!\n")
                
                # Parse the JSON string from the tool content
                try:
                    summary_text = content[0].get('text', '{}')
                    summary_data = json.loads(summary_text)
                    print(json.dumps(summary_data, indent=2))
                    
                    results_array = summary_data.get('results', [{}])
                    first_result = results_array[0] if len(results_array) > 0 else {}
                    
                    if first_result.get('node_count', 0) > 0:
                        print(f"\nGraph contains {first_result.get('node_count')} nodes and {first_result.get('edge_count')} edges! Verification successful.")
                    else:
                        print("\nGraph is currently EMPTY.")
                except Exception as parse_err:
                    print(f"Raw output:\n{content[0].get('text')}")
                    print(f"Failed to parse JSON output: {parse_err}")
            else:
                print("❌ No content returned from MCP Server.")
                
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == '__main__':
    main()
