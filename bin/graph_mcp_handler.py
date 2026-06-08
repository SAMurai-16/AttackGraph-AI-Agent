import sys
import os
import json
from splunk.persistconn.application import PersistentServerConnectionApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import networkx_tools

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
                result = networkx_tools.add_node_tool(
                    data.get('node_id'), data.get('label'), properties
                )
            elif action == 'add_edge':
                result = networkx_tools.add_edge_tool(
                    data.get('source_id'), data.get('target_id'), data.get('edge_type'), properties
                )
            elif action == 'get_patient_zero':
                result = networkx_tools.get_patient_zero_tool()
            elif action == 'get_shortest_path':
                result = networkx_tools.get_shortest_path_tool(
                    data.get('source_id'), data.get('target_id')
                )
            elif action == 'get_graph_summary':
                result = networkx_tools.get_graph_summary_tool()
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


