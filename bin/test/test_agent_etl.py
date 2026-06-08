import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from networkx_tools import add_node_tool, add_edge_tool, get_graph_summary_tool

# Load environment variables (GOOGLE_API_KEY must be set in .env)
load_dotenv()

# Convert our functions into LangChain tools
@tool
def add_node(node_id: str, label: str, properties: str) -> str:
    """Add a node to the knowledge graph. properties must be a valid JSON string."""
    try:
        props_dict = json.loads(properties)
    except Exception:
        props_dict = {}
    result = add_node_tool(node_id, label, props_dict)
    return json.dumps(result)

@tool
def add_edge(source_id: str, target_id: str, edge_type: str, properties: str) -> str:
    """Add a directed edge between two nodes. properties must be a valid JSON string."""
    try:
        props_dict = json.loads(properties)
    except Exception:
        props_dict = {}
    result = add_edge_tool(source_id, target_id, edge_type, props_dict)
    return json.dumps(result)

@tool
def get_graph_summary() -> str:
    """Get a summary of the current graph."""
    return json.dumps(get_graph_summary_tool())

# Mock Splunk Alert Data
MOCK_SPLUNK_ALERT = {
    "alert_id": "4812",
    "timestamp": "2026-06-06T10:05:00Z",
    "user": "alice",
    "src_host": "HR-LAPTOP-22",
    "src_ip": "10.0.1.55",
    "dest_ip": "185.44.1.2",
    "process": "powershell.exe",
    "action": "network_connection"
}

SYSTEM_PROMPT = """You are the AttackGraph AI Data Engineer.
Your job is to read raw JSON alerts from Splunk and convert them into an Attack Graph in NetworkX.
You must perform Named Entity Recognition (NER) on the JSON to identify:
- Users
- Hosts
- IPs
- Processes

Rules for NetworkX graph:
1. Use the add_node and add_edge tools to insert the data.
2. IMPORTANT: Every relationship MUST have a 'time' property extracted from the alert. Pass it as JSON string like '{"time": "2026-06-06T10:05:00Z"}'.
3. Use unique IDs for nodes. For users, use their name. For hosts, use hostname. For IPs, use the IP address.
4. Pass properties as valid JSON strings.

Example Flow:
1. add_node(node_id="alice", label="User", properties='{}')
2. add_node(node_id="HR-LAPTOP", label="Host", properties='{}')
3. add_edge(source_id="alice", target_id="HR-LAPTOP", edge_type="LOGGED_INTO", properties='{"time": "2026-06-06T10:05:00Z"}')
"""

def run_agent():
    # Initialize the LLM (Requires GOOGLE_API_KEY in environment)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    
    # Initialize the Agent with our custom NetworkX tools
    tools = [add_node, add_edge, get_graph_summary]
    # Initialize the LangGraph ReAct agent
    agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)
    
    print("\n--- Starting Agentic ETL Process ---")
    print("Received Splunk Alert:", json.dumps(MOCK_SPLUNK_ALERT, indent=2))
    print("\nAgent Reasoning:")
    
    prompt = f"Here is a new Splunk alert. Please extract the entities and relationships and insert them into the NetworkX graph.\n\nAlert: {json.dumps(MOCK_SPLUNK_ALERT)}\n\nAfter inserting, output the graph summary."
    
    try:
        result = agent.invoke({"messages": [("user", prompt)]})
        print("\nAgent Output:\n", result["messages"][-1].content)
        print("\n--- ETL Complete ---")
    except Exception as e:
        print("\nError during Agent Execution. Did you set GOOGLE_API_KEY in .env?")
        print(str(e))

if __name__ == "__main__":
    run_agent()
