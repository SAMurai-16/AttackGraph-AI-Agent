import sys
import os
import json
import splunk.rest

# Add the current directory to sys.path so we can import neo4j_tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import neo4j_tools

class Neo4jExecuteCypherHandler(splunk.rest.BaseRestHandler):
    def handle_POST(self):
        try:
            # Extract JSON payload from the request
            payload = self.request.get('payload', '')
            if payload:
                data = json.loads(payload)
            else:
                data = self.args

            query = data.get('query')
            if not query:
                self.response.setStatus(400)
                self.response.setHeader('content-type', 'application/json')
                self.response.write(json.dumps({"error": "Missing 'query' parameter."}))
                return

            # Execute the query using our existing tool
            result = neo4j_tools.execute_cypher_tool(query)
            
            self.response.setStatus(200)
            self.response.setHeader('content-type', 'application/json')
            self.response.write(json.dumps({"result": result}))
        except Exception as e:
            self.response.setStatus(500)
            self.response.setHeader('content-type', 'application/json')
            self.response.write(json.dumps({"error": str(e)}))

class Neo4jGetSchemaHandler(splunk.rest.BaseRestHandler):
    def handle_GET(self):
        try:
            # Get the schema using our existing tool
            schema = neo4j_tools.get_graph_schema_tool()
            
            self.response.setStatus(200)
            self.response.setHeader('content-type', 'application/json')
            self.response.write(json.dumps({"schema": schema}))
        except Exception as e:
            self.response.setStatus(500)
            self.response.setHeader('content-type', 'application/json')
            self.response.write(json.dumps({"error": str(e)}))
