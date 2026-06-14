import sys
import json
import urllib.request
import urllib.error
import ssl

sys.stdout.reconfigure(encoding='utf-8')

server_uri = "https://127.0.0.1:8089"
headers = {
    'Authorization': 'Basic c2FteWFrOklpaXRtQDIwMDU=', 
    'Content-Type': 'application/json'
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def call_splunk_tool(tool_name, arguments):

    payload = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    req = urllib.request.Request(
        f"{server_uri}/services/mcp",
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, context=ctx) as response:
        res_data = response.read().decode('utf-8')
        res_json = json.loads(res_data)
        if 'error' in res_json:
            raise Exception(res_json['error'])
        
        content = res_json.get('result', {}).get('content', [])
        if not content:
            raise Exception("No content returned")
            
        return json.loads(content[0]['text'])

def main():
    print("🚀 Starting AI Agent Investigation Pipeline...")
    
    # 1. Get Patient Zero
    print("\n[Step 1] Finding Patient Zero...")
    pz_res = call_splunk_tool("SplunkAgent_graph_get_patient_zero", {"action": "get_patient_zero"})
    patient_zeros = pz_res.get("results", [{}])[0].get("patient_zeros", [])
    
    if not patient_zeros:
        print("❌ No patient zero found in the graph. Aborting investigation.")
        sys.exit(1)
        
    # Get graph summary to find the latest activity
    summary_res = call_splunk_tool("SplunkAgent_graph_get_summary", {"action": "get_graph_summary"})
    edges = summary_res.get("results", [{}])[0].get("edges", [])
    
    latest_pz = patient_zeros[0]
    max_time = ""
    for u, v, data in edges:
        if u in patient_zeros and data.get("time", "") > max_time:
            max_time = data.get("time", "")
            latest_pz = u

    pz_id = latest_pz
    print(f"✅ Found Latest Patient Zero: {pz_id} (Activity: {max_time})")
    
    # 2. Generate Attack Path
    print("\n[Step 2] Tracing Attack Path...")
    path_res = call_splunk_tool("SplunkAgent_graph_generate_attack_path", {
        "action": "generate_attack_path",
        "patient_zero_id": pz_id
    })
    
    path_data = path_res.get("results", [{}])[0]
    attack_path = path_data.get("attack_path", [])
    path_score = path_data.get("path_score", {})
    all_hypotheses = path_data.get("all_hypotheses", [path_score])
    
    if not attack_path:
        print("❌ No valid attack path found from Patient Zero.")
        sys.exit(1)
        
    print(f"✅ Attack Path traced ({len(attack_path)} steps). Top Hypothesis: {path_score.get('attack')} ({path_score.get('probability')}%)")
    # 2.5 Get MITRE Mapping
    print("\n[Step 2.5] Mapping to MITRE ATT&CK...")
    mitre_res = call_splunk_tool("SplunkAgent_graph_map_mitre", {
        "action": "map_mitre",
        "attack_type": path_score.get('attack')
    })
    mitre_mapping = mitre_res.get("results", [{}])[0].get("mitre_mapping", {})
    
    # 3. Generate Incident Report (Writes to UI)
    print("\n[Step 3] Generating Incident Report & Pushing to Dashboard...")
    report_res = call_splunk_tool("SplunkAgent_graph_generate_incident_report", {
        "action": "generate_incident_report",
        "summary": f"The AI Agent investigated patient zero '{pz_id}' and successfully uncovered a verified {path_score.get('attack')} attack chain. Deep graph analysis confirms malicious activity with {path_score.get('probability')}% certainty.",
        "verdict": json.dumps(path_score),
        "attack_path": json.dumps(attack_path),
        "mitre": json.dumps(mitre_mapping),
        "all_hypotheses": json.dumps(all_hypotheses)
    })
    
    report_data = report_res.get("results", [{}])[0]
    print(f"✅ Report generated successfully: {report_data.get('report_id')}")
    print("\n🎉 Investigation Complete! The Dashboard UI has been instantly populated with the new verdicts.log data.")

if __name__ == '__main__':
    main()
