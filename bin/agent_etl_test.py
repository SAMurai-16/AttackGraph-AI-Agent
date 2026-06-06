import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from neo4j_tools import execute_cypher_tool, get_graph_schema_tool

# Load environment variables (GOOGLE_API_KEY must be set in .env)
load_dotenv()

# Convert our functions into LangChain tools
@tool
def execute_cypher(query: str) -> str:
    """Execute a Cypher query against the Neo4j database."""
    result = execute_cypher_tool(query)
    return json.dumps(result)

@tool
def get_graph_schema() -> str:
    """Get the current Neo4j graph schema (node labels and relationship types)."""
    return get_graph_schema_tool()

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
Your job is to read raw JSON alerts from Splunk and convert them into an Attack Graph in Neo4j.
You must perform Named Entity Recognition (NER) on the JSON to identify:
- Users
- Hosts
- IPs
- Processes

Rules for Neo4j Cypher:
1. Use the execute_cypher tool to insert the data.
2. IMPORTANT: Every relationship MUST have a 'time' property extracted from the alert.
3. Use MERGE instead of CREATE to avoid duplicating nodes.
4. If you don't know the schema, use the get_graph_schema tool first.

Example Cypher:
MERGE (u:User {name: 'alice'})
MERGE (h:Host {name: 'HR-LAPTOP'})
MERGE (u)-[:LOGGED_INTO {time: '2026-06-06T10:05:00Z'}]->(h)
"""

def run_agent():
    # Initialize the LLM (Requires GOOGLE_API_KEY in environment)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    
    # Initialize the Agent with our custom Neo4j tools
    tools = [execute_cypher, get_graph_schema]
    # Initialize the LangGraph ReAct agent
    agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)
    
    print("\n--- Starting Agentic ETL Process ---")
    print("Received Splunk Alert:", json.dumps(MOCK_SPLUNK_ALERT, indent=2))
    print("\nAgent Reasoning:")
    
    prompt = f"Here is a new Splunk alert. Please extract the entities and relationships and insert them into the Neo4j graph using Cypher.\n\nAlert: {json.dumps(MOCK_SPLUNK_ALERT)}"
    
    try:
        result = agent.invoke({"messages": [("user", prompt)]})
        print("\nAgent Output:\n", result["messages"][-1].content)
        print("\n--- ETL Complete ---")
    except Exception as e:
        print("\nError during Agent Execution. Did you set GOOGLE_API_KEY in .env?")
        print(str(e))

if __name__ == "__main__":
    run_agent()
