import sys
import json
import urllib.request
import urllib.error
import ssl
import os
import logging

from seed_handlers import ddos, cloud_identity, brute_force, malware_ransomware, lateral_movement

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed_graph")

HANDLERS = {
    "ddos":               ddos.extract,
    "cloud_identity":     cloud_identity.extract,
    "brute_force":        brute_force.extract,
    "malware_ransomware": malware_ransomware.extract,
    "lateral_movement":   lateral_movement.extract,
}

def main():
    # Splunk passes the alert payload via standard input
    payload_str = sys.stdin.read()
    if not payload_str:
        print("ERROR: No payload received from Splunk.", file=sys.stderr)
        sys.exit(1)
        

    try:
        payload = json.loads(payload_str)
    except Exception as e:
        print(f"ERROR: Invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(2)
        
    session_key = payload.get('session_key')
    server_uri = payload.get('server_uri', 'https://127.0.0.1:8089')
    result = payload.get('result', {})
    
    # Extract config parameters we set in savedsearches.conf
    config = payload.get('configuration', {})
    attack_type = config.get('attack_type', 'unclassified')
    severity = config.get('severity', 'medium')
    search_name = payload.get('search_name', 'Unknown_Alert')
    
    if not session_key:
        print("ERROR: No session key in payload.", file=sys.stderr)
        sys.exit(3)

    # Route to the correct extraction handler
    handler = HANDLERS.get(attack_type)
    if not handler:
        print(f"ERROR: No handler for attack_type={attack_type}. Payload: {config}", file=sys.stderr)
        sys.exit(4)

    # Extract nodes and edges
    graph_payload = handler(result, severity)
    nodes_to_add = graph_payload.get("nodes", [])
    edges_to_add = graph_payload.get("edges", [])

    # Now send them to our MCP Graph Server natively
    from dotenv import load_dotenv
    import base64
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    splunk_user = os.environ.get("SPLUNK_USERNAME", "admin")
    splunk_pass = os.environ.get("SPLUNK_PASSWORD", "admin")
    auth_b64 = base64.b64encode(f"{splunk_user}:{splunk_pass}".encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f'Basic {auth_b64}',
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
                return json.loads(res_data)
        except Exception as e:
            print(f"ERROR: Graph Call failed: {e}", file=sys.stderr)
            return None

    # Add source_alert to all edge properties automatically
    for edge in edges_to_add:
        if "attrs" not in edge:
            edge["attrs"] = {}
        edge["attrs"]["source_alert"] = search_name

    # 1. Add all nodes
    for node in nodes_to_add:
        call_graph_endpoint({
            "action": "add_node",
            "node_id": node["id"],
            "label": node["type"],
            "properties": node.get("attrs", {})
        })
        
    # 2. Add all edges
    for edge in edges_to_add:
        call_graph_endpoint({
            "action": "add_edge",
            "source_id": edge["src"],
            "target_id": edge["dst"],
            "edge_type": edge["rel"],
            "properties": edge.get("attrs", {})
        })
        
    print(f"INFO: Successfully pushed {len(nodes_to_add)} nodes and {len(edges_to_add)} edges to AttackGraph Memory.")

if __name__ == "__main__":
    main()
