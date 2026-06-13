import requests
import json


SPLUNK_HOST = "localhost"
SPLUNK_PORT = 8089
USERNAME = "samyak"
PASSWORD = "Iiitm@2005"
BASE_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}"

def register_networkx_tools():
    url = f"{BASE_URL}/services/mcp_tools/batch_replace"
    
    # We map all graph operations to the same Splunk REST endpoint, using the "action" field in the schema.
    # This prevents us from having to restart Splunk to register new restmap.conf endpoints!
    tools = [
        {
            "name": "graph_add_node",
            "title": "Graph: Add Node",
            "description": "Add a node to the NetworkX knowledge graph. Does not support Cypher.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_node"],
                        "description": "Must be 'add_node'"
                    },
                    "node_id": {"type": "string"},
                    "label": {"type": "string"},
                    "properties": {"type": "object"}
                },
                "required": ["action", "node_id", "label"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "node_id": "$node_id$",
                        "label": "$label$",
                        "properties": "$properties$"
                    }
                }
            }
        },
        {
            "name": "graph_add_edge",
            "title": "Graph: Add Edge",
            "description": "Add an edge between two nodes in the NetworkX graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_edge"],
                        "description": "Must be 'add_edge'"
                    },
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"},
                    "edge_type": {"type": "string"},
                    "properties": {"type": "object"}
                },
                "required": ["action", "source_id", "target_id", "edge_type"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "source_id": "$source_id$",
                        "target_id": "$target_id$",
                        "edge_type": "$edge_type$",
                        "properties": "$properties$"
                    }
                }
            }
        },
        {
            "name": "graph_get_patient_zero",
            "title": "Graph: Get Patient Zero",
            "description": "Finds nodes in the graph with no incoming edges.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_patient_zero"]
                    }
                },
                "required": ["action"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$"
                    }
                }
            }
        },
        {
            "name": "graph_get_summary",
            "title": "Graph: Get Summary",
            "description": "Returns all nodes and edges in the graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_graph_summary"]
                    }
                },
                "required": ["action"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$"
                    }
                }
            }
        },
        {
            "name": "graph_get_neighbours",
            "title": "Graph: Get Neighbours",
            "description": "Get the predecessors and successors of a specific node.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_neighbours"]
                    },
                    "node_id": {"type": "string"}
                },
                "required": ["action", "node_id"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "node_id": "$node_id$"
                    }
                }
            }
        },
        {
            "name": "graph_reset",
            "title": "Graph: Reset",
            "description": "Wipe the entire graph clean.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reset_graph"]
                    }
                },
                "required": ["action"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$"
                    }
                }
            }
        },
        {
            "name": "graph_get_shortest_path",
            "title": "Graph: Get Shortest Path",
            "description": "Finds the shortest path between a source and target node.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_shortest_path"]
                    },
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"}
                },
                "required": ["action", "source_id", "target_id"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "source_id": "$source_id$",
                        "target_id": "$target_id$"
                    }
                }
            }
        },
        {
            "name": "graph_get_investigation_playbook",
            "title": "Graph: Get Investigation Playbook",
            "description": "Returns the evidence tags and weights for a given attack type to guide the AI investigation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["get_investigation_playbook"]
                    },
                    "attack_type": {"type": "string"}
                },
                "required": ["action", "attack_type"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "attack_type": "$attack_type$"
                    }
                }
            }
        },
        {
            "name": "graph_score_hypotheses",
            "title": "Graph: Score Hypotheses",
            "description": "Calculates the mathematical probability for all attack patterns based on evidence tags found in the graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["score_hypotheses"]
                    }
                },
                "required": ["action"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$"
                    }
                }
            }
        },
        {
            "name": "graph_map_mitre",
            "title": "Graph: Map MITRE",
            "description": "Returns MITRE ATT&CK tactic and technique IDs for a given attack type.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["map_mitre"]
                    },
                    "attack_type": {"type": "string"}
                },
                "required": ["action", "attack_type"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "attack_type": "$attack_type$"
                    }
                }
            }
        },
        {
            "name": "graph_generate_attack_path",
            "title": "Graph: Generate Attack Path",
            "description": "Builds a time-ordered attack chain from patient zero, filtering for edges with evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate_attack_path"]
                    },
                    "patient_zero_id": {"type": "string"}
                },
                "required": ["action", "patient_zero_id"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "patient_zero_id": "$patient_zero_id$"
                    }
                }
            }
        },
        {
            "name": "graph_generate_incident_report",
            "title": "Graph: Generate Incident Report",
            "description": "Compiles incident data into a Markdown and JSON report hosted natively in the Splunk App.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate_incident_report"]
                    },
                    "summary": {"type": "string"},
                    "verdict": {"type": "object"},
                    "attack_path": {"type": "array"},
                    "mitre": {"type": "object"},
                    "all_hypotheses": {"type": "array"}
                },
                "required": ["action", "summary"]
            },
            "_meta": {
                "execution": {
                    "type": "api",
                    "method": "POST",
                    "endpoint": "services/graph_execute_operation",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "action": "$action$",
                        "summary": "$summary$",
                        "verdict": "$verdict$",
                        "attack_path": "$attack_path$",
                        "mitre": "$mitre$",
                        "all_hypotheses": "$all_hypotheses$"
                    }
                }
            }
        }
    ]

    payload = {
        "external_app_id": "SplunkAgent",
        "tools": tools
    }

    print("Registering NetworkX tools to Splunk_MCP_Server...")
    response = requests.post(
        url,
        auth=(USERNAME, PASSWORD),
        json=payload,
        verify=False
    )
    
    if response.status_code in (200, 201):
        print("✅ Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    register_networkx_tools()
