import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables if present
load_dotenv()

# Default to the docker-compose settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "hackathon2026")

class Neo4jConnector:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_cypher(self, query: str, parameters: dict = None) -> list:
        """
        Executes a Cypher query against the Neo4j database and returns the result as a list of dictionaries.
        
        Args:
            query (str): The Cypher query string to execute.
            parameters (dict, optional): A dictionary of parameters to pass to the query.
            
        Returns:
            list: The query results.
        """
        if parameters is None:
            parameters = {}
            
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            return [{"error": str(e)}]

    def get_graph_schema(self) -> str:
        """
        Retrieves the current schema of the Neo4j graph, including node labels and relationship types.
        Useful for providing context to an LLM before it writes Cypher queries.
        
        Returns:
            str: A formatted string describing the node labels and relationships in the database.
        """
        try:
            with self.driver.session() as session:
                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                
                # Get relationship types
                rels_result = session.run("CALL db.relationshipTypes()")
                relationships = [record["relationshipType"] for record in rels_result]
                
                schema = (
                    f"Graph Schema:\n"
                    f"Node Labels: {', '.join(labels) if labels else 'None yet'}\n"
                    f"Relationship Types: {', '.join(relationships) if relationships else 'None yet'}"
                )
                return schema
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"

# Singleton instance for easy import in other files
db = Neo4jConnector()

def execute_cypher_tool(query: str) -> list:
    """Wrapper function for LLM tool calling."""
    return db.execute_cypher(query)

def get_graph_schema_tool() -> str:
    """Wrapper function for LLM tool calling."""
    return db.get_graph_schema()

if __name__ == "__main__":
    # Test connection
    print("Testing Neo4j Connection...")
    schema = db.get_graph_schema()
    print(schema)
