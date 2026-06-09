"""
Database Query Optimization
Indexes, query optimization, connection pooling, and query caching
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Union
from functools import wraps
import hashlib
import json

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("psycopg2 not available - using placeholder implementations")


class QueryCache:
    """
    Simple in-memory query cache with TTL
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize query cache
        
        Args:
            max_size: Maximum number of cached queries
            default_ttl: Default time-to-live in seconds
        """
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, query: str, params: Optional[tuple] = None) -> str:
        """Generate cache key from query and parameters"""
        key_str = f"{query}:{params}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """Get cached result"""
        key = self._generate_key(query, params)
        
        if key in self.cache:
            result, timestamp, ttl = self.cache[key]
            if time.time() - timestamp < ttl:
                self.hits += 1
                return result
            else:
                # Expired
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, query: str, result: Any, params: Optional[tuple] = None, ttl: Optional[int] = None):
        """Cache query result"""
        if ttl is None:
            ttl = self.default_ttl
        
        key = self._generate_key(query, params)
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (result, time.time(), ttl)
    
    def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }


class ConnectionPool:
    """
    Database connection pool manager
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connection pool
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.pool = None
        
        if PSYCOPG2_AVAILABLE:
            self._create_pool()
    
    def _create_pool(self):
        """Create connection pool"""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.get('min_connections', 2),
                maxconn=self.config.get('max_connections', 10),
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database', 'risk_db'),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                connect_timeout=self.config.get('timeout', 10)
            )
            print(f"Connection pool created: {self.config.get('min_connections', 2)}-{self.config.get('max_connections', 10)} connections")
        except Exception as e:
            print(f"Failed to create connection pool: {e}")
    
    def get_connection(self):
        """Get connection from pool"""
        if self.pool:
            return self.pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()


class IndexManager:
    """
    Database index management
    """
    
    # Recommended indexes for risk analysis system
    RECOMMENDED_INDEXES = [
        # Entities table
        {
            'table': 'entities',
            'name': 'idx_entities_type',
            'columns': ['entity_type'],
            'type': 'btree'
        },
        {
            'table': 'entities',
            'name': 'idx_entities_sector',
            'columns': ['sector'],
            'type': 'btree'
        },
        {
            'table': 'entities',
            'name': 'idx_entities_rating',
            'columns': ['credit_rating'],
            'type': 'btree'
        },
        # Relationships table
        {
            'table': 'relationships',
            'name': 'idx_relationships_source',
            'columns': ['source_id'],
            'type': 'btree'
        },
        {
            'table': 'relationships',
            'name': 'idx_relationships_target',
            'columns': ['target_id'],
            'type': 'btree'
        },
        {
            'table': 'relationships',
            'name': 'idx_relationships_type',
            'columns': ['relationship_type'],
            'type': 'btree'
        },
        {
            'table': 'relationships',
            'name': 'idx_relationships_composite',
            'columns': ['source_id', 'target_id', 'relationship_type'],
            'type': 'btree'
        },
        # Risk scores table
        {
            'table': 'risk_scores',
            'name': 'idx_risk_scores_entity',
            'columns': ['entity_id'],
            'type': 'btree'
        },
        {
            'table': 'risk_scores',
            'name': 'idx_risk_scores_timestamp',
            'columns': ['timestamp'],
            'type': 'btree'
        },
        {
            'table': 'risk_scores',
            'name': 'idx_risk_scores_composite',
            'columns': ['entity_id', 'timestamp'],
            'type': 'btree'
        },
        # Alerts table
        {
            'table': 'alerts',
            'name': 'idx_alerts_entity',
            'columns': ['entity_id'],
            'type': 'btree'
        },
        {
            'table': 'alerts',
            'name': 'idx_alerts_severity',
            'columns': ['severity'],
            'type': 'btree'
        },
        {
            'table': 'alerts',
            'name': 'idx_alerts_status',
            'columns': ['status'],
            'type': 'btree'
        },
        {
            'table': 'alerts',
            'name': 'idx_alerts_timestamp',
            'columns': ['created_at'],
            'type': 'btree'
        }
    ]
    
    @staticmethod
    def create_index(conn, index_def: Dict[str, Any]) -> bool:
        """
        Create database index
        
        Args:
            conn: Database connection
            index_def: Index definition
        
        Returns:
            Success status
        """
        try:
            cursor = conn.cursor()
            
            columns_str = ', '.join(index_def['columns'])
            index_type = index_def.get('type', 'btree')
            
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_def['name']}
            ON {index_def['table']} USING {index_type} ({columns_str})
            """
            
            cursor.execute(query)
            conn.commit()
            cursor.close()
            
            print(f"Created index: {index_def['name']}")
            return True
            
        except Exception as e:
            print(f"Failed to create index {index_def['name']}: {e}")
            return False
    
    @staticmethod
    def create_all_indexes(conn):
        """Create all recommended indexes"""
        success_count = 0
        
        for index_def in IndexManager.RECOMMENDED_INDEXES:
            if IndexManager.create_index(conn, index_def):
                success_count += 1
        
        print(f"Created {success_count}/{len(IndexManager.RECOMMENDED_INDEXES)} indexes")
        return success_count
    
    @staticmethod
    def analyze_table(conn, table_name: str):
        """Run ANALYZE on table to update statistics"""
        try:
            cursor = conn.cursor()
            cursor.execute(f"ANALYZE {table_name}")
            conn.commit()
            cursor.close()
            print(f"Analyzed table: {table_name}")
        except Exception as e:
            print(f"Failed to analyze table {table_name}: {e}")
    
    @staticmethod
    def get_index_usage(conn, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get index usage statistics
        
        Args:
            conn: Database connection
            table_name: Optional table name filter
        
        Returns:
            List of index usage statistics
        """
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            """
            
            if table_name:
                query += f" WHERE tablename = '{table_name}'"
            
            query += " ORDER BY idx_scan DESC"
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Failed to get index usage: {e}")
            return []


class QueryOptimizer:
    """
    Query optimization utilities
    """
    
    @staticmethod
    def explain_query(conn, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Get query execution plan
        
        Args:
            conn: Database connection
            query: SQL query
            params: Query parameters
        
        Returns:
            Execution plan
        """
        try:
            cursor = conn.cursor()
            
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE) {query}"
            
            if params:
                cursor.execute(explain_query, params)
            else:
                cursor.execute(explain_query)
            
            plan = cursor.fetchone()[0]
            cursor.close()
            
            return plan[0] if plan else {}
            
        except Exception as e:
            print(f"Failed to explain query: {e}")
            return {}
    
    @staticmethod
    def optimize_query(query: str) -> str:
        """
        Apply basic query optimizations
        
        Args:
            query: Original query
        
        Returns:
            Optimized query
        """
        optimized = query
        
        # Add LIMIT if not present for large result sets
        if 'LIMIT' not in optimized.upper() and 'SELECT' in optimized.upper():
            # Only for SELECT queries without aggregations
            if 'COUNT' not in optimized.upper() and 'SUM' not in optimized.upper():
                optimized += ' LIMIT 1000'
        
        # Suggest using EXISTS instead of COUNT for existence checks
        if 'COUNT(*)' in optimized and 'WHERE' in optimized.upper():
            print("Tip: Consider using EXISTS instead of COUNT(*) for existence checks")
        
        return optimized
    
    @staticmethod
    def batch_insert(conn, table: str, columns: List[str], data: List[tuple]) -> bool:
        """
        Optimized batch insert
        
        Args:
            conn: Database connection
            table: Table name
            columns: Column names
            data: List of tuples with values
        
        Returns:
            Success status
        """
        try:
            cursor = conn.cursor()
            
            # Use COPY for large batches (more efficient than INSERT)
            if len(data) > 100:
                from io import StringIO
                
                # Create CSV buffer
                buffer = StringIO()
                for row in data:
                    buffer.write('\t'.join(str(v) for v in row) + '\n')
                buffer.seek(0)
                
                # Use COPY
                cursor.copy_from(buffer, table, columns=columns)
            else:
                # Use executemany for smaller batches
                placeholders = ','.join(['%s'] * len(columns))
                columns_str = ','.join(columns)
                query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                cursor.executemany(query, data)
            
            conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Batch insert failed: {e}")
            conn.rollback()
            return False


class DatabaseOptimizer:
    """
    Main database optimization coordinator
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database optimizer
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.query_cache = QueryCache(
            max_size=config.get('cache_size', 1000),
            default_ttl=config.get('cache_ttl', 300)
        )
        self.query_times = []
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute query with caching and optimization
        
        Args:
            query: SQL query
            params: Query parameters
            use_cache: Whether to use cache
            cache_ttl: Cache TTL override
        
        Returns:
            Query results
        """
        # Check cache
        if use_cache:
            cached_result = self.query_cache.get(query, params)
            if cached_result is not None:
                return cached_result
        
        # Execute query
        conn = self.connection_pool.get_connection()
        if not conn:
            return None
        
        try:
            start_time = time.time()
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            
            # Convert to list of dicts
            results_list = [dict(row) for row in results]
            
            # Cache results
            if use_cache:
                self.query_cache.set(query, results_list, params, cache_ttl)
            
            return results_list
            
        except Exception as e:
            print(f"Query execution failed: {e}")
            return None
        finally:
            self.connection_pool.return_connection(conn)
    
    def setup_indexes(self):
        """Set up all recommended indexes"""
        conn = self.connection_pool.get_connection()
        if conn:
            try:
                IndexManager.create_all_indexes(conn)
            finally:
                self.connection_pool.return_connection(conn)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.query_cache.get_stats()
        
        avg_query_time = sum(self.query_times) / len(self.query_times) if self.query_times else 0
        
        return {
            'cache': cache_stats,
            'avg_query_time': avg_query_time,
            'total_queries': len(self.query_times),
            'connection_pool': {
                'min_connections': self.config.get('min_connections', 2),
                'max_connections': self.config.get('max_connections', 10)
            }
        }
    
    def close(self):
        """Close all connections"""
        self.connection_pool.close_all()


# Decorator for query caching
def cached_query(ttl: int = 300):
    """
    Decorator to cache query results
    
    Args:
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{args}:{kwargs}"
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            # Check cache
            if key_hash in cache:
                result, timestamp = cache[key_hash]
                if time.time() - timestamp < ttl:
                    return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache[key_hash] = (result, time.time())
            
            return result
        
        return wrapper
    return decorator


# Global optimizer instance
_db_optimizer = None

def get_database_optimizer(config: Optional[Dict[str, Any]] = None):
    """Get global database optimizer instance"""
    global _db_optimizer
    if _db_optimizer is None and config:
        _db_optimizer = DatabaseOptimizer(config)
    return _db_optimizer

# Made with Bob
