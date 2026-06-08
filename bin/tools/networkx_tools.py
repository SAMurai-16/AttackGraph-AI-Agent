import networkx as nx
import json

# Global in-memory graph that will persist as long as the Splunk persistconn python process is alive!
G = nx.MultiDiGraph()

def add_node_tool(node_id: str, label: str, properties: dict) -> dict:
    """Add a node to the knowledge graph."""
    properties['label'] = label
    G.add_node(node_id, **properties)
    return {"status": "success", "node_id": node_id, "properties": properties}

def add_edge_tool(source_id: str, target_id: str, edge_type: str, properties: dict) -> dict:
    """Add a directed edge between two nodes."""
    # Ensure nodes exist
    if not G.has_node(source_id):
        G.add_node(source_id, label="Unknown")
    if not G.has_node(target_id):
        G.add_node(target_id, label="Unknown")
        
    properties['edge_type'] = edge_type
    G.add_edge(source_id, target_id, **properties)
    return {"status": "success", "source_id": source_id, "target_id": target_id, "edge_type": edge_type}

def get_patient_zero_tool() -> dict:
    """Find patient zero (nodes with in-degree 0)."""
    patient_zeros = [n for n, in_degree in G.in_degree() if in_degree == 0]
    return {"status": "success", "patient_zeros": patient_zeros}

def get_shortest_path_tool(source_id: str, target_id: str) -> dict:
    """Find shortest path between two nodes."""
    try:
        path = nx.shortest_path(G, source=source_id, target=target_id)
        return {"status": "success", "path": path}
    except nx.NetworkXNoPath:
        return {"status": "error", "message": f"No path found between {source_id} and {target_id}"}
    except nx.NodeNotFound as e:
        return {"status": "error", "message": str(e)}

def get_graph_summary_tool() -> dict:
    """Get a summary of the current graph."""
    return {
        "status": "success",
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "nodes": list(G.nodes(data=True)),
        "edges": list(G.edges(data=True))
    }
