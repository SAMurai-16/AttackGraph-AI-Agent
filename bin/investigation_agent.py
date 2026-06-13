import os
import json
import urllib.request
import urllib.error
import ssl
import time

# Splunk sets a broken SSL_CERT_FILE environment variable by default.
# We must remove it so the Google GenAI SDK uses its own certificates.
os.environ.pop('SSL_CERT_FILE', None)

from dotenv import load_dotenv

# LangChain and LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

# Load API keys
load_dotenv()

SPLUNK_URI = 'https://127.0.0.1:8089'
# Using the test user for the MCP server connection
HEADERS = {
    'Authorization': 'Basic c2FteWFrOklpaXRtQDIwMDU=', # samyak:Iiitm@2005
    'Content-Type': 'application/json'
}

# Ignore local self-signed certs
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Helper function to call a tool on the Splunk MCP Server."""
    req_data = {
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    req = urllib.request.Request(
        f"{SPLUNK_URI}/services/mcp",
        data=json.dumps(req_data).encode('utf-8'),
        headers=HEADERS,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            # The result from MCP tools is usually buried in structuredContent
            try:
                # Extract the actual data from the MCP response envelope
                content = res_data.get('result', {}).get('structuredContent', {})
                return content
            except Exception:
                return res_data
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------
# Define LangChain Tools (Wrapping the MCP Endpoints)
# ---------------------------------------------------------

@tool
def splunk_search(query: str) -> dict:
    """Run a raw SPL search against Splunk to find logs or user activity. 
    Ensure your query is valid SPL (e.g., '| makeresults | eval user="Alice"')."""
    print(f"\n[AI RUNNING SPLUNK SEARCH] -> {query}")
    return call_mcp_tool("splunk_run_query", {"query": query})

@tool
def get_graph_summary() -> dict:
    """Get a summary of all nodes and edges currently in the Attack Graph."""
    print(f"\n[AI READING GRAPH SUMMARY]")
    return call_mcp_tool("SplunkAgent_graph_get_summary", {"action": "get_graph_summary"})

@tool
def add_graph_node(node_id: str, label: str, properties: dict = None) -> dict:
    """Add an entity (like a User or IP) to the Attack Graph."""
    if properties is None:
        properties = {}
    print(f"\n[AI ADDING NODE] -> {label}: {node_id}")
    return call_mcp_tool("SplunkAgent_graph_add_node", {
        "action": "add_node",
        "node_id": node_id,
        "label": label,
        "properties": properties
    })

@tool
def add_graph_edge(source_id: str, target_id: str, relationship: str, properties: dict = None) -> dict:
    """Connect two entities in the Attack Graph with a relationship (e.g., FAILED_LOGIN)."""
    if properties is None:
        properties = {}
    print(f"\n[AI ADDING EDGE] -> {source_id} --[{relationship}]--> {target_id}")
    return call_mcp_tool("SplunkAgent_graph_add_edge", {
        "action": "add_edge",
        "source_id": source_id,
        "target_id": target_id,
        "relationship": relationship,
        "properties": properties
    })

def main():
    print("Initializing Proactive Investigation Agent...")
    
    # 1. Initialize Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    # 2. Provide the tools
    tools = [splunk_search, get_graph_summary, add_graph_node, add_graph_edge]
    
    # 3. Create the ReAct Agent
    agent_executor = create_react_agent(llm, tools)
    
    # 4. Give the Agent a Mission
    system_prompt = """You are an elite Cyber Threat Hunting AI working inside Splunk.
    Your job is to proactively investigate threats by combining log data with a NetworkX Knowledge Graph.
    
    You have the ability to:
    1. Search Splunk directly using the splunk_search tool to find missing evidence.
    2. Read the existing graph memory using get_graph_summary.
    3. Add new evidence you find into the graph using add_graph_node and add_graph_edge.
    
    Always document what you find by adding it to the graph.
    """
    
    # Let's give it a test mission
    test_mission = """
    Mission: Please check the current Knowledge Graph to see who is in it. 
    Then, run a Splunk search to find recent internal Splunk activity using this exact query: 
    `search index=_internal sourcetype=splunkd | head 5`
    
    Extract any IP addresses or component names from those real logs, add them as nodes to the graph, and finally tell me the updated graph summary.
    """
    
    print(f"\nAssigning Mission: {test_mission}")
    print("-" * 50)
    
    # Run the Agent
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=test_mission)
    ]
    
    for event in agent_executor.stream({"messages": messages}):
        for value in event.values():
            if "messages" in value:
                for msg in value["messages"]:
                    if msg.content:
                        print(f"\n🤖 AI: {msg.content}")

if __name__ == "__main__":
    main()
