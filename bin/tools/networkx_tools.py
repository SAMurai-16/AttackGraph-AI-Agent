import networkx as nx
import json

import os

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "graph.json")

def _load_graph():
    if os.path.exists(GRAPH_FILE):
        try:
            with open(GRAPH_FILE, 'r') as f:
                data = json.load(f)
                return nx.node_link_graph(data)
        except:
            pass
    return nx.MultiDiGraph()

def _save_graph(g):
    with open(GRAPH_FILE, 'w') as f:
        json.dump(nx.node_link_data(g), f)

# Initialize
G = _load_graph()

def add_node_tool(node_id: str, label: str, properties: dict) -> dict:
    """Add a node to the knowledge graph."""
    global G
    G = _load_graph()
    properties['label'] = label
    G.add_node(node_id, **properties)
    _save_graph(G)
    return {"status": "success", "node_id": node_id, "properties": properties}

def add_edge_tool(source_id: str, target_id: str, edge_type: str, properties: dict) -> dict:
    """Add a directed edge between two nodes."""
    global G
    G = _load_graph()
    # Ensure nodes exist
    if not G.has_node(source_id):
        G.add_node(source_id, label="Unknown")
    if not G.has_node(target_id):
        G.add_node(target_id, label="Unknown")
        
    properties['edge_type'] = edge_type
    G.add_edge(source_id, target_id, **properties)
    _save_graph(G)
    return {"status": "success", "source_id": source_id, "target_id": target_id, "edge_type": edge_type}

def get_patient_zero_tool() -> dict:
    """Find patient zero (nodes with in-degree 0), sorted by latest activity."""
    global G
    G = _load_graph()
    patient_zeros = [n for n, in_degree in G.in_degree() if in_degree == 0]
    
    # Sort by the most recent outgoing edge time
    def get_latest_time(node):
        max_time = ""
        for _, _, data in G.out_edges(node, data=True):
            if data.get('time', '') > max_time:
                max_time = data.get('time', '')
        return max_time

    patient_zeros.sort(key=get_latest_time, reverse=True)
    return {"status": "success", "patient_zeros": patient_zeros}

def get_shortest_path_tool(source_id: str, target_id: str) -> dict:
    """Find shortest path between two nodes."""
    global G
    G = _load_graph()
    try:
        path = nx.shortest_path(G, source=source_id, target=target_id)
        return {"status": "success", "path": path}
    except nx.NetworkXNoPath:
        return {"status": "error", "message": f"No path found between {source_id} and {target_id}"}
    except nx.NodeNotFound as e:
        return {"status": "error", "message": str(e)}

def get_graph_summary_tool() -> dict:
    """Get a summary of the current graph."""
    global G
    G = _load_graph()
    return {
        "status": "success",
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "nodes": list(G.nodes(data=True)),
        "edges": list(G.edges(data=True))
    }

def get_neighbours_tool(node_id: str) -> dict:
    """Get the predecessors and successors of a specific node."""
    global G
    G = _load_graph()
    if not G.has_node(node_id):
        return {"status": "error", "message": f"Node {node_id} not found in graph."}
    
    successors = list(G.successors(node_id))
    predecessors = list(G.predecessors(node_id))
    
    return {
        "status": "success",
        "node_id": node_id,
        "successors": successors,
        "predecessors": predecessors
    }

def reset_graph_tool() -> dict:
    """Wipe the entire graph clean (for testing)."""
    global G
    G = nx.MultiDiGraph()
    _save_graph(G)
    return {"status": "success", "message": "Graph has been completely wiped."}

PATTERNS = {
    "ddos": {
        "high_packet_rate":       30,
        "multiple_source_ips":    25,
        "syn_flood":              20,
        "udp_amplification":      15,
        "target_unavailability":  10,
    },
    "cloud_identity": {
        "impossible_travel":          35,
        "new_device_user_agent":      20,
        "mass_api_calls":             20,
        "privilege_escalation_call":  15,
        "oauth_token_reuse":          10,
    },
    "brute_force": {
        "failed_logins":           15,
        "new_device":              20,
        "credential_dumping_tool": 30,
        "password_spray_pattern":  25,
        "hash_passing_event":      10,
    },
    "malware_ransomware": {
        "encoded_powershell":    25,
        "office_macro_spawn":    25,
        "c2_beacon":             20,
        "mass_file_encryption":  30,
        "shadow_copy_deletion":  20,
        "known_hash_ioc":        10,
    },
    "lateral_movement": {
        "multi_host_logon":       25,
        "psexec_usage":           30,
        "wmi_remote_execution":   25,
        "rdp_to_new_host":        20,
        "pass_the_ticket":        10,
    },
}

def get_investigation_playbook_tool(attack_type: str) -> dict:
    """Return the evidence tags and weights to guide the AI investigation without giving exact queries."""
    if attack_type not in PATTERNS:
        return {"status": "error", "message": f"Unknown attack type: {attack_type}"}
    return {
        "status": "success",
        "attack_type": attack_type,
        "evidence_weights": PATTERNS[attack_type]
    }

def score_hypotheses_tool() -> dict:
    """For each attack pattern, scan graph edges for evidence tags, compute score and normalise to probability."""
    global G
    G = _load_graph()
    
    observed_evidence = set()
    for _, _, data in G.edges(data=True):
        ev = data.get("evidence")
        if ev:
            observed_evidence.add(ev)

    results = []
    for attack, weights in PATTERNS.items():
        hit_evidence    = {e: w for e, w in weights.items() if e in observed_evidence}
        score           = sum(hit_evidence.values())
        total_possible  = sum(weights.values())
        probability     = round((score / total_possible) * 100, 1) if total_possible else 0

        results.append({
            "attack":      attack,
            "probability": probability,
            "score":       score,
            "max_score":   total_possible,
            "evidence":    list(hit_evidence.keys()),
            "missing":     [e for e in weights if e not in observed_evidence],
        })

    results.sort(key=lambda x: x["probability"], reverse=True)
    return {
        "status": "success",
        "hypotheses": results, 
        "top": results[0] if results else None
    }

MITRE_MAP = {
    "ddos": {
        "tactics":    ["Impact"],
        "techniques": [
            {"id": "T1498",     "name": "Network Denial of Service"},
            {"id": "T1498.001", "name": "Direct Network Flood"},
            {"id": "T1498.002", "name": "Reflection Amplification"},
            {"id": "T1499",     "name": "Endpoint Denial of Service"},
        ]
    },
    "cloud_identity": {
        "tactics":    ["Initial Access", "Persistence", "Collection"],
        "techniques": [
            {"id": "T1078.004", "name": "Valid Accounts: Cloud Accounts"},
            {"id": "T1110.003", "name": "Password Spraying"},
            {"id": "T1098.003", "name": "Account Manipulation: Add Cloud Account"},
            {"id": "T1530",     "name": "Data from Cloud Storage"},
        ]
    },
    "brute_force": {
        "tactics":    ["Credential Access"],
        "techniques": [
            {"id": "T1110",     "name": "Brute Force"},
            {"id": "T1110.001", "name": "Password Guessing"},
            {"id": "T1110.003", "name": "Password Spraying"},
            {"id": "T1003",     "name": "OS Credential Dumping"},
            {"id": "T1550.002", "name": "Pass the Hash"},
        ]
    },
    "malware_ransomware": {
        "tactics":    ["Execution", "Command and Control", "Impact"],
        "techniques": [
            {"id": "T1566.001", "name": "Spear Phishing Attachment"},
            {"id": "T1059.001", "name": "PowerShell"},
            {"id": "T1071.001", "name": "Application Layer Protocol"},
            {"id": "T1486",     "name": "Data Encrypted for Impact"},
            {"id": "T1490",     "name": "Inhibit System Recovery"},
        ]
    },
    "lateral_movement": {
        "tactics":    ["Lateral Movement"],
        "techniques": [
            {"id": "T1021.001", "name": "Remote Desktop Protocol"},
            {"id": "T1021.002", "name": "SMB/Windows Admin Shares"},
            {"id": "T1047",     "name": "WMI Remote Execution"},
            {"id": "T1569.002", "name": "System Services: Service Execution"},
            {"id": "T1550.003", "name": "Pass the Ticket"},
        ]
    },
}

def map_mitre_tool(attack_type: str) -> dict:
    """Return MITRE tactic and technique IDs for a given attack type."""
    if attack_type not in MITRE_MAP:
        return {"status": "error", "message": f"No MITRE mapping found for attack type: {attack_type}"}
    
    return {
        "status": "success",
        "attack_type": attack_type,
        "mitre_mapping": MITRE_MAP[attack_type]
    }

def generate_attack_path_tool(patient_zero_id: str, earliest_time: str = None, latest_time: str = None) -> dict:
    """Build a time-ordered attack chain from patient zero, filtering for edges with evidence."""
    from datetime import datetime
    
    global G
    G = _load_graph()
    
    if not G.has_node(patient_zero_id):
        return {"status": "error", "message": f"Patient zero node '{patient_zero_id}' not found in graph."}

    visited = set()
    queue = [patient_zero_id]
    chain = []
    path_evidence = set()
    
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        
        # Traverse outbound edges
        for nxt in G.successors(node):
            # For MultiDiGraph, get all edge dicts between node and nxt
            edge_data_dict = G.get_edge_data(node, nxt)
            if not edge_data_dict:
                continue
                
            for key, edge in edge_data_dict.items():
                # TIME FILTER: Only include edges within the specified time bounds
                edge_time = edge.get("time", "")
                if earliest_time and edge_time < earliest_time:
                    continue
                if latest_time and edge_time > latest_time:
                    continue
                    
                # EVIDENCE FILTER: Only include edges that have an evidence tag!
                if not edge.get("evidence"):
                    continue
                    
                path_evidence.add(edge.get("evidence"))
                    
                chain.append({
                    "from":      node,
                    "to":        nxt,
                    "relation":  edge.get("edge_type", "UNKNOWN"),
                    "time":      edge.get("time", "T+?"),
                    "evidence":  edge.get("evidence"),
                    "severity":  edge.get("severity", "unknown")
                })
                # Add destination to queue
                if nxt not in visited and nxt not in queue:
                    queue.append(nxt)

    # Sort by timestamp
    def _ts(step):
        try:
            return datetime.fromisoformat(step["time"].replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    chain.sort(key=_ts)
    
    # Calculate subgraph score based solely on this path's evidence
    path_scores = []
    for attack, weights in PATTERNS.items():
        hit_evidence    = {e: w for e, w in weights.items() if e in path_evidence}
        score           = sum(hit_evidence.values())
        total_possible  = sum(weights.values())
        probability     = round((score / total_possible) * 100, 1) if total_possible else 0
        path_scores.append({
            "attack":      attack,
            "probability": probability,
            "score":       score,
            "max_score":   total_possible,
            "evidence":    list(hit_evidence.keys()),
            "missing":     [e for e in weights if e not in path_evidence],
        })
    path_scores.sort(key=lambda x: x["probability"], reverse=True)
    top_score = path_scores[0] if path_scores else None

    return {
        "status": "success",
        "patient_zero_id": patient_zero_id,
        "path_score": top_score,
        "attack_path": chain,
        "all_hypotheses": path_scores
    }

def generate_incident_report_tool(summary: str, verdict: dict, attack_path: list, mitre: dict, all_hypotheses: list = None) -> dict:
    """Generate final incident report, save as JSON and Markdown, and return download URLs."""
    import time
    import json
    from pathlib import Path
    
    report_id = f"IR-{int(time.time())}"
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    report = {
        "report_id": report_id,
        "generated_at": generated_at,
        "verdict": verdict,
        "summary": summary,
        "attack_path": attack_path,
        "mitre": mitre,
        "all_hypotheses": all_hypotheses or []
    }
    
    # Path to Splunk App static directory
    static_dir = Path(__file__).resolve().parent.parent.parent / "appserver" / "static" / "reports"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    json_path = static_dir / f"{report_id}.json"
    json_path.write_text(json.dumps(report, indent=2))
    
    # Write Markdown
    md_content = f"# Incident Report: {report_id}\n\n"
    md_content += f"**Generated:** {generated_at}\n\n"
    md_content += f"## Executive Summary\n{summary}\n\n"
    
    if verdict:
        md_content += f"## Verdict\n"
        md_content += f"- **Attack Type:** {verdict.get('attack', 'Unknown')}\n"
        md_content += f"- **Probability:** {verdict.get('probability', 0)}%\n"
        md_content += f"- **Evidence Found:** {', '.join(verdict.get('evidence', []))}\n\n"
        
    if mitre:
        md_content += f"## MITRE ATT&CK Mapping\n"
        md_content += f"- **Tactics:** {', '.join(mitre.get('tactics', []))}\n"
        for t in mitre.get('techniques', []):
            md_content += f"  - [{t.get('id')}] {t.get('name')}\n"
        md_content += "\n"
        
    if attack_path:
        md_content += f"## Attack Timeline\n"
        for step in attack_path:
            md_content += f"- **{step.get('time')}**: `{step.get('from')}` -> `{step.get('relation')}` -> `{step.get('to')}` (Evidence: {step.get('evidence')})\n"
            
    md_path = static_dir / f"{report_id}.md"
    md_path.write_text(md_content)
    
    # Master index for dashboard
    index_path = static_dir / "index.json"
    index_data = []
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text())
        except:
            pass
    
    index_data.append({
        "report_id": report_id,
        "generated_at": generated_at,
        "summary": summary,
        "verdict": verdict.get('attack', 'Unknown') if verdict else 'Unknown',
        "json_url": f"/en-US/static/app/SplunkAgent/reports/{report_id}.json",
        "md_url": f"/en-US/static/app/SplunkAgent/reports/{report_id}.md"
    })
    index_path.write_text(json.dumps(index_data, indent=2))
    
    # Write to Splunk Monitored Log for Dashboard Studio UI
    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    verdict_log_path = logs_dir / "verdicts.log"
    
    v_attack = verdict.get("attack", "Unknown") if verdict else "Unknown"
    v_conf = verdict.get("probability", 0) if verdict else 0
    domain = "Unclassified"
    if v_attack in ["ddos", "lateral_movement"]: domain = "Network"
    elif v_attack in ["cloud_identity", "brute_force"]: domain = "Identity"
    elif v_attack in ["malware_ransomware"]: domain = "Endpoint"
    
    patient_zero = attack_path[0].get("from") if attack_path else "unknown"
    impacted_asset = attack_path[-1].get("to") if attack_path else "unknown"
    
    techniques = [t.get("id") for t in mitre.get("techniques", [])] if mitre else []
    evidence = list(set(step.get("evidence") for step in attack_path if step.get("evidence")))
    graph_edges = [{"source": step.get("from"), "relationship": step.get("relation"), "target": step.get("to")} for step in attack_path]
    
    verdict_payload = {
        "alert_id": report_id,
        "_time": int(time.time()),
        "verdict": v_attack,
        "confidence": v_conf,
        "summary": summary,
        "domain": domain,
        "patient_zero": patient_zero,
        "impacted_asset": impacted_asset,
        "techniques": techniques,
        "evidence": evidence,
        "attack_path": attack_path,
        "graph_edges": graph_edges,
        "hypotheses": all_hypotheses or []
    }
    
    with open(verdict_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(verdict_payload) + "\n")
    
    return {
        "status": "success",
        "report_id": report_id,
        "json_download": f"/en-US/static/app/SplunkAgent/reports/{report_id}.json",
        "markdown_download": f"/en-US/static/app/SplunkAgent/reports/{report_id}.md",
        "message": "Report generated successfully and is available in the Splunk UI."
    }


def get_historical_investigations_tool(patient_zero_id: str) -> dict:
    """Retrieve summarized context of past AI investigations involving this entity."""
    import json
    from pathlib import Path

    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    verdict_log_path = logs_dir / "verdicts.log"
    
    if not verdict_log_path.exists():
        return {"status": "success", "history": []}
        
    history = []
    try:
        with open(verdict_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    record = json.loads(line)
                    if record.get('patient_zero') == patient_zero_id:
                        history.append({
                            "alert_id": record.get('alert_id'),
                            "time": record.get('_time'),
                            "verdict": record.get('verdict'),
                            "confidence": record.get('confidence'),
                            "impacted_asset": record.get('impacted_asset'),
                            "summary": record.get('summary')
                        })
                except:
                    continue
    except Exception as e:
        return {"status": "error", "message": f"Failed to read verdicts.log: {str(e)}"}
        
    # Sort by time descending (newest first)
    history.sort(key=lambda x: x.get('time', 0), reverse=True)
    
    return {
        "status": "success", 
        "patient_zero_id": patient_zero_id,
        "history": history
    }
