import sys
import json
import urllib.request
import urllib.error
import ssl

def main():
    # Splunk passes the alert payload via standard input
    payload_str = sys.stdin.read()
    if not payload_str:
        print("ERROR: No payload received from Splunk.", file=sys.stderr)
        sys.exit(1)
        
    # DEBUG: Write the exact payload to a file so we can see what Splunk is sending
    import os
    debug_path = os.path.join(os.path.dirname(__file__), "debug_payload.json")
    with open(debug_path, "w") as f:
        f.write(payload_str)
        
    try:
        payload = json.loads(payload_str)
    except Exception as e:
        print(f"ERROR: Invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(2)
        
    session_key = payload.get('session_key')
    server_uri = payload.get('server_uri', 'https://127.0.0.1:8089')
    result = payload.get('result', {})
    search_name = payload.get('search_name', 'Unknown_Alert')
    
    if not session_key:
        print("ERROR: No session key in payload.", file=sys.stderr)
        sys.exit(3)
        
    # We will look for common entity fields
    user = result.get('user') or result.get('username') or result.get('src_user')
    src_ip = result.get('src_ip') or result.get('src')
    dest_ip = result.get('dest_ip') or result.get('dest')
    
    nodes_to_add = []
    edges_to_add = []
    
    if user:
        nodes_to_add.append({"id": user, "label": "User", "props": {}})
    if src_ip:
        nodes_to_add.append({"id": src_ip, "label": "IP", "props": {"type": "source"}})
    if dest_ip:
        nodes_to_add.append({"id": dest_ip, "label": "IP", "props": {"type": "destination"}})
        
    # Create relationships based on what we found
    if user and src_ip:
        edges_to_add.append({"source": user, "target": src_ip, "relation": search_name})
    if src_ip and dest_ip:
        edges_to_add.append({"source": src_ip, "target": dest_ip, "relation": search_name})
    if user and dest_ip:
        edges_to_add.append({"source": user, "target": dest_ip, "relation": search_name})
        
    # Now send them to our MCP Graph Server
    headers = {
        'Authorization': 'Basic c2FteWFrOklpaXRtQDIwMDU=', # samyak:Iiitm@2005
        'Content-Type': 'application/json'
    }
    
    # Ignore self-signed cert warnings for local Splunk
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    def call_graph_endpoint(payload_dict):
        req = urllib.request.Request(
            f"{server_uri}/services/graph_execute_operation",
            data=json.dumps(payload_dict).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                res_data = response.read().decode('utf-8')
                with open(os.path.join(os.path.dirname(__file__), "debug_mcp.json"), "a") as f:
                    f.write(f"\\n--- graph_execute_operation ---\\n" + res_data)
                return json.loads(res_data)
        except Exception as e:
            with open(os.path.join(os.path.dirname(__file__), "debug_mcp.json"), "a") as f:
                f.write(f"\\n--- graph_execute_operation ERROR ---\\n" + str(e))
            print(f"ERROR: Graph Call failed: {e}", file=sys.stderr)
            return None

    # Extract rich context for the edges (the events)
    timestamp = result.get('_time') or result.get('time')
    event_code = result.get('EventCode') or result.get('signature_id') or result.get('event_id')
    action = result.get('action') or result.get('status') or result.get('vendor_action')
    severity = result.get('severity') or result.get('risk_score')
    process_name = result.get('Process_Name') or result.get('process') or result.get('app')
    
    edge_props = {
        "source_alert": search_name
    }
    if timestamp: edge_props["time"] = timestamp
    if event_code: edge_props["event_code"] = event_code
    if action: edge_props["action"] = action
    if severity: edge_props["severity"] = severity
    if process_name: edge_props["process_name"] = process_name

    # 1. Add all nodes
    for node in nodes_to_add:
        call_graph_endpoint({
            "action": "add_node",
            "node_id": node["id"],
            "label": node["label"],
            "properties": node["props"]
        })
        
    # 2. Add all edges
    for edge in edges_to_add:
        call_graph_endpoint({
            "action": "add_edge",
            "source_id": edge["source"],
            "target_id": edge["target"],
            "edge_type": edge["relation"],
            "properties": edge_props
        })
        
    print("INFO: Successfully pushed alert entities to AttackGraph Memory.")

if __name__ == "__main__":
    main()
