"""
Neo4j Graph Database Connector
Provides connection management and query execution for Neo4j database
"""

import os
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import json

try:
    from neo4j import GraphDatabase, Driver, Session, Result
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    if TYPE_CHECKING:
        from neo4j import GraphDatabase, Driver, Session, Result

logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Neo4j graph database connector"""
    
    def __init__(
        self,
        uri: str = 'bolt://localhost:7687',
        user: str = 'neo4j',
        password: str = 'password',
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50,
        connection_acquisition_timeout: int = 60
    ):
        """
        Initialize Neo4j connector
        
        Args:
            uri: Neo4j connection URI
            user: Database user
            password: Database password
            max_connection_lifetime: Maximum connection lifetime in seconds
            max_connection_pool_size: Maximum connections in pool
            connection_acquisition_timeout: Timeout for acquiring connection
        """
        if not NEO4J_AVAILABLE:
            raise RuntimeError("neo4j driver is not installed. Install with: pip install neo4j")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None
        
        self.config = {
            'max_connection_lifetime': max_connection_lifetime,
            'max_connection_pool_size': max_connection_pool_size,
            'connection_acquisition_timeout': connection_acquisition_timeout
        }
        
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize Neo4j driver"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                **self.config
            )
            # Test connection
            if self.driver:
                self.driver.verify_connectivity()
            logger.info(f"Neo4j driver initialized: {self.uri}")
        except Exception as e:
            # Catch all exceptions including ServiceUnavailable and AuthError
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query
            parameters: Query parameters
            database: Database name
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")
        
        with self.driver.session(database=database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Execute a write transaction
        
        Args:
            query: Cypher query
            parameters: Query parameters
            database: Database name
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")
        
        def _execute_write_tx(tx):
            result = tx.run(query, parameters or {})
            return [dict(record) for record in result]
        
        with self.driver.session(database=database) as session:
            return session.execute_write(_execute_write_tx)
    
    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Execute a read transaction
        
        Args:
            query: Cypher query
            parameters: Query parameters
            database: Database name
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")
        
        def _execute_read_tx(tx):
            result = tx.run(query, parameters or {})
            return [dict(record) for record in result]
        
        with self.driver.session(database=database) as session:
            return session.execute_read(_execute_read_tx)
    
    def create_node(
        self,
        labels: List[str],
        properties: Dict[str, Any],
        database: str = 'neo4j'
    ) -> Dict[str, Any]:
        """
        Create a node
        
        Args:
            labels: Node labels
            properties: Node properties
            database: Database name
            
        Returns:
            Created node properties
        """
        labels_str = ':'.join(labels)
        query = f"""
            CREATE (n:{labels_str} $properties)
            RETURN n
        """
        
        results = self.execute_write(query, {'properties': properties}, database)
        return results[0]['n'] if results else {}
    
    def create_relationship(
        self,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
        database: str = 'neo4j'
    ) -> Dict[str, Any]:
        """
        Create a relationship between two nodes
        
        Args:
            from_node: Source node match criteria
            to_node: Target node match criteria
            rel_type: Relationship type
            properties: Relationship properties
            database: Database name
            
        Returns:
            Created relationship properties
        """
        query = f"""
            MATCH (a), (b)
            WHERE a.entity_id = $from_id AND b.entity_id = $to_id
            CREATE (a)-[r:{rel_type} $properties]->(b)
            RETURN r
        """
        
        params = {
            'from_id': from_node.get('entity_id'),
            'to_id': to_node.get('entity_id'),
            'properties': properties or {}
        }
        
        results = self.execute_write(query, params, database)
        return results[0]['r'] if results else {}
    
    def find_nodes(
        self,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Find nodes matching criteria
        
        Args:
            labels: Node labels to match
            properties: Properties to match
            limit: Maximum number of results
            database: Database name
            
        Returns:
            List of matching nodes
        """
        labels_str = ':'.join(labels) if labels else ''
        
        where_clauses = []
        if properties:
            where_clauses = [f"n.{k} = ${k}" for k in properties.keys()]
        
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''
        
        query = f"""
            MATCH (n{':' + labels_str if labels_str else ''})
            {where_str}
            RETURN n
            LIMIT {limit}
        """
        
        results = self.execute_read(query, properties or {}, database)
        return [record['n'] for record in results]
    
    def find_paths(
        self,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
        rel_types: Optional[List[str]] = None,
        max_depth: int = 3,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Find paths between two nodes
        
        Args:
            from_node: Source node match criteria
            to_node: Target node match criteria
            rel_types: Relationship types to traverse
            max_depth: Maximum path depth
            database: Database name
            
        Returns:
            List of paths
        """
        rel_str = '|'.join(rel_types) if rel_types else ''
        rel_pattern = f"[:{rel_str}*1..{max_depth}]" if rel_str else f"[*1..{max_depth}]"
        
        query = f"""
            MATCH path = (a)-{rel_pattern}-(b)
            WHERE a.entity_id = $from_id AND b.entity_id = $to_id
            RETURN path, length(path) as path_length
            ORDER BY path_length
        """
        
        params = {
            'from_id': from_node.get('entity_id'),
            'to_id': to_node.get('entity_id')
        }
        
        return self.execute_read(query, params, database)
    
    def get_neighbors(
        self,
        node: Dict[str, Any],
        rel_types: Optional[List[str]] = None,
        direction: str = 'both',
        limit: int = 100,
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Get neighboring nodes
        
        Args:
            node: Node to find neighbors for
            rel_types: Relationship types to traverse
            direction: 'in', 'out', or 'both'
            limit: Maximum number of results
            database: Database name
            
        Returns:
            List of neighboring nodes
        """
        rel_str = '|'.join(rel_types) if rel_types else ''
        
        if direction == 'out':
            pattern = f"-[:{rel_str}]->" if rel_str else "-[]->"
        elif direction == 'in':
            pattern = f"<-[:{rel_str}]-" if rel_str else "<-[]-"
        else:  # both
            pattern = f"-[:{rel_str}]-" if rel_str else "-[]-"
        
        query = f"""
            MATCH (n){pattern}(neighbor)
            WHERE n.entity_id = $entity_id
            RETURN DISTINCT neighbor
            LIMIT {limit}
        """
        
        results = self.execute_read(
            query,
            {'entity_id': node.get('entity_id')},
            database
        )
        return [record['neighbor'] for record in results]
    
    def update_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
        database: str = 'neo4j'
    ) -> Dict[str, Any]:
        """
        Update node properties
        
        Args:
            node_id: Node entity_id
            properties: Properties to update
            database: Database name
            
        Returns:
            Updated node properties
        """
        set_clauses = [f"n.{k} = ${k}" for k in properties.keys()]
        set_str = ', '.join(set_clauses)
        
        query = f"""
            MATCH (n {{entity_id: $entity_id}})
            SET {set_str}, n.updated_at = datetime()
            RETURN n
        """
        
        params = {'entity_id': node_id, **properties}
        results = self.execute_write(query, params, database)
        return results[0]['n'] if results else {}
    
    def delete_node(
        self,
        node_id: str,
        detach: bool = True,
        database: str = 'neo4j'
    ) -> int:
        """
        Delete a node
        
        Args:
            node_id: Node entity_id
            detach: Whether to detach relationships first
            database: Database name
            
        Returns:
            Number of nodes deleted
        """
        detach_str = 'DETACH ' if detach else ''
        query = f"""
            MATCH (n {{entity_id: $entity_id}})
            {detach_str}DELETE n
            RETURN count(n) as deleted_count
        """
        
        results = self.execute_write(query, {'entity_id': node_id}, database)
        return results[0]['deleted_count'] if results else 0
    
    def run_algorithm(
        self,
        algorithm: str,
        config: Dict[str, Any],
        database: str = 'neo4j'
    ) -> List[Dict[str, Any]]:
        """
        Run a graph algorithm
        
        Args:
            algorithm: Algorithm name (e.g., 'pageRank', 'louvain')
            config: Algorithm configuration
            database: Database name
            
        Returns:
            Algorithm results
        """
        query = f"CALL gds.{algorithm}.stream($config)"
        return self.execute_read(query, {'config': config}, database)
    
    def get_database_stats(self, database: str = 'neo4j') -> Dict[str, Any]:
        """
        Get database statistics
        
        Args:
            database: Database name
            
        Returns:
            Database statistics
        """
        queries = {
            'node_count': "MATCH (n) RETURN count(n) as count",
            'relationship_count': "MATCH ()-[r]->() RETURN count(r) as count",
            'label_counts': "MATCH (n) RETURN labels(n) as labels, count(*) as count",
            'relationship_type_counts': "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
        }
        
        stats = {}
        for key, query in queries.items():
            results = self.execute_read(query, database=database)
            stats[key] = results
        
        return stats
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful
        """
        try:
            if not self.driver:
                return False
            # Test with a simple query instead of verify_connectivity
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                return record is not None and record['test'] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the driver"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class Neo4jRepository:
    """Base repository class for graph operations"""
    
    def __init__(self, connector: Neo4jConnector):
        """
        Initialize repository
        
        Args:
            connector: Neo4j connector instance
        """
        self.connector = connector
    
    def _serialize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize properties for Neo4j"""
        serialized = {}
        for key, value in properties.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value
        return serialized
    
    def _deserialize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize properties from Neo4j"""
        deserialized = {}
        for key, value in properties.items():
            if isinstance(value, str):
                try:
                    deserialized[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    deserialized[key] = value
            else:
                deserialized[key] = value
        return deserialized


# Example usage and testing
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize connector
    connector = Neo4jConnector(
        uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        user=os.getenv('NEO4J_USER', 'neo4j'),
        password=os.getenv('NEO4J_PASSWORD', 'password')
    )
    
    try:
        # Test connection
        if connector.test_connection():
            print("✓ Connection successful")
        
        # Get database stats
        stats = connector.get_database_stats()
        print(f"✓ Database stats: {stats['node_count']}")
        
        # Find some nodes
        portfolios = connector.find_nodes(labels=['Portfolio'], limit=5)
        print(f"✓ Found {len(portfolios)} portfolios")
        
    finally:
        connector.close()

# Made with Bob
