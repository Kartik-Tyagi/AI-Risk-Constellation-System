"""
PostgreSQL Database Connector
Provides connection pooling and query execution for PostgreSQL database
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from contextlib import contextmanager
from datetime import datetime
import json

try:
    import psycopg2
    from psycopg2 import pool, extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    if TYPE_CHECKING:
        import psycopg2
        from psycopg2 import pool, extras
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)


class PostgreSQLConnector:
    """PostgreSQL database connector with connection pooling"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str = 'risk_constellation',
        user: str = 'postgres',
        password: str = 'postgres',
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Initialize PostgreSQL connector
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is not installed. Install with: pip install psycopg2-binary")
        
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_pool: Optional[Any] = None
        
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize connection pool"""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                **self.config
            )
            logger.info(f"PostgreSQL connection pool initialized (min={self.min_connections}, max={self.max_connections})")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool
        
        Yields:
            Database connection
        """
        if not self.connection_pool:
            raise RuntimeError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get a cursor from a pooled connection
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
            
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Cursor error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        """
        Execute a query and optionally fetch results
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_query_dict(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as dictionaries
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of dictionaries
        """
        with self.get_cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    
    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> None:
        """
        Execute a query multiple times with different parameters
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def insert_one(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[str] = None
    ) -> Optional[Any]:
        """
        Insert a single row
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs
            returning: Column to return (e.g., 'id')
            
        Returns:
            Value of returning column if specified
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        if returning:
            query += f" RETURNING {returning}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, tuple(data.values()))
            if returning:
                result = cursor.fetchone()
                return result[0] if result else None
            return None
    
    def insert_many(
        self,
        table: str,
        data_list: List[Dict[str, Any]]
    ) -> None:
        """
        Insert multiple rows
        
        Args:
            table: Table name
            data_list: List of dictionaries
        """
        if not data_list:
            return
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['%s'] * len(data_list[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        params_list = [tuple(data.values()) for data in data_list]
        self.execute_many(query, params_list)
    
    def update_one(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """
        Update a single row
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs to update
            where: Dictionary of column: value pairs for WHERE clause
            
        Returns:
            Number of rows updated
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(list(data.values()) + list(where.values()))
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def delete_one(
        self,
        table: str,
        where: Dict[str, Any]
    ) -> int:
        """
        Delete rows
        
        Args:
            table: Table name
            where: Dictionary of column: value pairs for WHERE clause
            
        Returns:
            Number of rows deleted
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, tuple(where.values()))
            return cursor.rowcount
    
    def bulk_insert(
        self,
        table: str,
        data_list: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> None:
        """
        Bulk insert with batching for large datasets
        
        Args:
            table: Table name
            data_list: List of dictionaries
            batch_size: Number of rows per batch
        """
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            self.insert_many(table, batch)
            logger.debug(f"Inserted batch {i//batch_size + 1} ({len(batch)} rows)")
    
    def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        conflict_columns: List[str],
        update_columns: Optional[List[str]] = None
    ) -> None:
        """
        Insert or update (upsert) using ON CONFLICT
        
        Args:
            table: Table name
            data: Dictionary of column: value pairs
            conflict_columns: Columns that define uniqueness
            update_columns: Columns to update on conflict (default: all except conflict columns)
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        conflict = ', '.join(conflict_columns)
        
        if update_columns is None:
            update_columns = [k for k in data.keys() if k not in conflict_columns]
        
        update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        
        query = f"""
            INSERT INTO {table} ({columns}) 
            VALUES ({placeholders})
            ON CONFLICT ({conflict}) 
            DO UPDATE SET {update_set}
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, tuple(data.values()))
    
    def get_table_stats(self, table: str) -> Dict[str, Any]:
        """
        Get statistics for a table
        
        Args:
            table: Table name
            
        Returns:
            Dictionary with table statistics
        """
        query = f"""
            SELECT 
                COUNT(*) as row_count,
                pg_size_pretty(pg_total_relation_size('{table}')) as total_size,
                pg_size_pretty(pg_relation_size('{table}')) as table_size,
                pg_size_pretty(pg_indexes_size('{table}')) as indexes_size
        """
        
        result = self.execute_query_dict(query)
        return result[0] if result else {}
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class PostgreSQLRepository:
    """Base repository class for database operations"""
    
    def __init__(self, connector: PostgreSQLConnector):
        """
        Initialize repository
        
        Args:
            connector: PostgreSQL connector instance
        """
        self.connector = connector
    
    def _serialize_json(self, obj: Any) -> str:
        """Serialize object to JSON string"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.dumps(obj)
    
    def _deserialize_json(self, json_str: str) -> Any:
        """Deserialize JSON string to object"""
        return json.loads(json_str) if json_str else None


# Example usage and testing
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize connector
    connector = PostgreSQLConnector(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'risk_constellation'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    
    try:
        # Test connection
        if connector.test_connection():
            print("✓ Connection successful")
        
        # Example queries
        users = connector.execute_query_dict("SELECT * FROM users LIMIT 5")
        print(f"✓ Found {len(users)} users")
        
        # Get table stats
        stats = connector.get_table_stats('users')
        print(f"✓ Users table: {stats}")
        
    finally:
        connector.close()

# Made with Bob
