import sys
import os
import json
from splunk.persistconn.application import PersistentServerConnectionApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import tools

class GraphExecuteOperationHandler(PersistentServerConnectionApplication):
    def __init__(self, command_line=None, command_arg=None):
        super(GraphExecuteOperationHandler, self).__init__()

    def handle(self, in_string):
        try:
            req = json.loads(in_string)
            method = req.get("method", "GET")
            
            if method != "POST":
                return {"payload": {"error": "Only POST is supported"}, "status": 405}
                
            payload_str = req.get("payload", "{}")
            data = json.loads(payload_str) if payload_str else {}

            action = data.get('action')
            
            # Robustly parse properties if Splunk_MCP_Server stringified them
            properties = data.get('properties', {})
            if isinstance(properties, str):
                import ast
                try:
                    properties = ast.literal_eval(properties)
                except Exception:
                    try:
                        properties = json.loads(properties)
                    except Exception:
                        properties = {}
            if not isinstance(properties, dict):
                properties = {}
                
            result = {}
            
            if action == 'add_node':
                result = tools.add_node_tool(
                    data.get('node_id'), data.get('label'), properties
                )
            elif action == 'add_edge':
                result = tools.add_edge_tool(
                    data.get('source_id'), data.get('target_id'), data.get('edge_type'), properties
                )
            elif action == 'get_patient_zero':
                result = tools.get_patient_zero_tool()
            elif action == 'get_shortest_path':
                result = tools.get_shortest_path_tool(
                    data.get('source_id'), data.get('target_id')
                )
            elif action == 'get_graph_summary':
                result = tools.get_graph_summary_tool()
            elif action == 'get_neighbours':
                result = tools.get_neighbours_tool(data.get('node_id'))
            elif action == 'reset_graph':
                result = tools.reset_graph_tool()
            elif action == 'get_investigation_playbook':
                result = tools.get_investigation_playbook_tool(data.get('attack_type'))
            elif action == 'score_hypotheses':
                result = tools.score_hypotheses_tool()
            elif action == 'map_mitre':
                result = tools.map_mitre_tool(data.get('attack_type'))
            elif action == 'generate_attack_path':
                result = tools.generate_attack_path_tool(data.get('patient_zero_id'))
            elif action == 'get_historical_investigations':
                result = tools.get_historical_investigations_tool(data.get('patient_zero_id'))
            elif action == 'get_system_prompt':
                result = tools.get_system_prompt_tool()
            elif action == 'generate_incident_report':
                import ast
                
                verdict = data.get('verdict')
                if isinstance(verdict, str):
                    try: verdict = json.loads(verdict)
                    except: verdict = ast.literal_eval(verdict) if verdict else {}
                
                attack_path = data.get('attack_path')
                if isinstance(attack_path, str):
                    try: attack_path = json.loads(attack_path)
                    except: attack_path = ast.literal_eval(attack_path) if attack_path else []
                    
                mitre = data.get('mitre')
                if isinstance(mitre, str):
                    try: mitre = json.loads(mitre)
                    except: mitre = ast.literal_eval(mitre) if mitre else {}

                all_hypotheses = data.get('all_hypotheses')
                if isinstance(all_hypotheses, str):
                    try: all_hypotheses = json.loads(all_hypotheses)
                    except: all_hypotheses = ast.literal_eval(all_hypotheses) if all_hypotheses else []

                result = tools.generate_incident_report_tool(
                    data.get('summary'),
                    verdict,
                    attack_path,
                    mitre,
                    all_hypotheses
                )
            else:
                return {"payload": json.dumps({"error": f"Unknown action: {action}", "req": req, "data": data}), "status": 400}
            
            # Use json.dumps explicitly to ensure the framework doesn't crash on dicts
            return {
                "payload": json.dumps(result), 
                "status": 200,
                "headers": {"Content-Type": "application/json"}
            }
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {
                "payload": json.dumps({"error": str(e), "traceback": tb, "in_string_preview": str(in_string)[:200]}), 
                "status": 500,
                "headers": {"Content-Type": "application/json"}
            }


