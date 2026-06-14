import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    # 1. Get the Splunk Auth Token from the environment
    token = os.environ.get("SPLUNK_TOKEN")
    if not token:
        print("ERROR: SPLUNK_TOKEN environment variable is not set.")
        print("Please set it before running: set SPLUNK_TOKEN=your_token_here")
        return

    url = "https://127.0.0.1:8089/services/mcp"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"Connecting to Splunk MCP Server at {url}...")
    
    with httpx.Client(verify=False) as client:
        # 2. Discover available tools
        print("Fetching available tools from Splunk...")
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        response = client.post(url, headers=headers, json=payload, timeout=30.0)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return
            
        data = response.json()
        if "error" in data:
            print(f"❌ MCP Error: {data['error']}")
            return
            
        tools = data.get("result", {}).get("tools", [])
        
        print("\nSearching for graph_add_node...")
        target_tool_name = None
        for tool in tools:
            if "graph_add_node" in tool.get("name", ""):
                target_tool_name = tool["name"]
                break
                
        if target_tool_name:
            print(f"Found our target tool: {target_tool_name}")
            print("Executing Graph Add Node...")
            
            call_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {
                    "name": target_tool_name,
                    "arguments": {
                        "action": "add_node",
                        "node_id": "test_user_1",
                        "label": "User",
                        "properties": {"name": "Alice"}
                    }
                }
            }
            try:
                print("\nExecuting Graph Add Node...")
                call_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_add_node",
                        "arguments": {
                            "action": "add_node",
                            "node_id": "test_user_1",
                            "label": "User",
                            "properties": {"name": "Alice"}
                        }
                    }
                }
                call_res = client.post(url, headers=headers, json=call_payload, timeout=60.0)
                call_data = call_res.json()
                print("\n✅ Success! Result from NetworkX:")
                print(json.dumps(call_data, indent=2))
                
                print("\nExecuting Graph Get Playbook...")
                playbook_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_get_investigation_playbook",
                        "arguments": {
                            "action": "get_investigation_playbook",
                            "attack_type": "brute_force"
                        }
                    }
                }
                playbook_res = client.post(url, headers=headers, json=playbook_payload, timeout=60.0)
                print("\n✅ Success! Playbook Result:")
                print(json.dumps(playbook_res.json(), indent=2))
                
                print("\nExecuting Graph Score Hypotheses...")
                score_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_score_hypotheses",
                        "arguments": {
                            "action": "score_hypotheses"
                        }
                    }
                }
                score_res = client.post(url, headers=headers, json=score_payload, timeout=60.0)
                print("\n✅ Success! Score Hypotheses Result:")
                print(json.dumps(score_res.json(), indent=2))
                
                print("\nExecuting Graph Map MITRE...")
                mitre_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_map_mitre",
                        "arguments": {
                            "action": "map_mitre",
                            "attack_type": "brute_force"
                        }
                    }
                }
                mitre_res = client.post(url, headers=headers, json=mitre_payload, timeout=60.0)
                print("\n✅ Success! Map MITRE Result:")
                print(json.dumps(mitre_res.json(), indent=2))
                
                print("\nExecuting Graph Add Node 2...")
                node2_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_add_node",
                        "arguments": {
                            "action": "add_node",
                            "node_id": "10.0.0.5",
                            "label": "Server",
                            "properties": {
                                "name": "DB Server"
                            }
                        }
                    }
                }
                client.post(url, headers=headers, json=node2_payload, timeout=60.0)
                
                print("\nExecuting Graph Add Edge (with evidence)...")
                edge_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_add_edge",
                        "arguments": {
                            "action": "add_edge",
                            "source_id": "test_user_1",
                            "target_id": "10.0.0.5",
                            "edge_type": "SSH_LOGIN",
                            "properties": {
                                "evidence": "failed_logins",
                                "time": "2026-06-12T14:30:00Z"
                            }
                        }
                    }
                }
                client.post(url, headers=headers, json=edge_payload, timeout=60.0)
                
                print("\nExecuting Graph Generate Attack Path...")
                path_payload = {
                    "method": "tools/call",
                    "params": {
                        "name": "SplunkAgent_graph_generate_attack_path",
                        "arguments": {
                            "action": "generate_attack_path",
                            "patient_zero_id": "test_user_1"
                        }
                    }
                }
                path_res = client.post(url, headers=headers, json=path_payload, timeout=60.0)
                print("\n✅ Success! Attack Path Result:")
                print(json.dumps(path_res.json(), indent=2))
                
            except Exception as tool_err:
                print(f"\n❌ Tool Request Failed: {tool_err}")
        else:
            print("❌ Error: Could not find any tool containing 'graph' in the name.")
            print("Make sure the registration was successful and the Splunk MCP Server is healthy.")

if __name__ == "__main__":
    main()
