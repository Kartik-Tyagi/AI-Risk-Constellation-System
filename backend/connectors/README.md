# Database Connectors

This module provides database connection management and query execution for PostgreSQL and Neo4j databases.

## Overview

The connectors provide:
- **Connection pooling** for efficient resource management
- **Context managers** for safe connection handling
- **Type-safe query execution** with proper error handling
- **Repository pattern** base classes for data access layers
- **Bulk operations** for high-performance data ingestion

## PostgreSQL Connector

### Features

- Thread-safe connection pooling using `psycopg2.pool.ThreadedConnectionPool`
- Dictionary-based result sets with `RealDictCursor`
- Bulk insert operations with batching
- Upsert support using `ON CONFLICT`
- Transaction management
- Table statistics and monitoring

### Usage

```python
from backend.connectors import PostgreSQLConnector

# Initialize connector
connector = PostgreSQLConnector(
    host='localhost',
    port=5432,
    database='risk_constellation',
    user='postgres',
    password='postgres',
    min_connections=1,
    max_connections=10
)

# Execute query
users = connector.execute_query_dict(
    "SELECT * FROM users WHERE role = %s",
    ('admin',)
)

# Insert data
user_id = connector.insert_one(
    'users',
    {
        'username': 'john_doe',
        'email': 'john@example.com',
        'password_hash': 'hashed_password',
        'role': 'analyst'
    },
    returning='user_id'
)

# Bulk insert
connector.bulk_insert(
    'market_data',
    market_data_list,
    batch_size=1000
)

# Upsert
connector.upsert(
    'counterparties',
    {
        'counterparty_id': 'CP001',
        'counterparty_name': 'Bank Corp',
        'credit_rating': 'AA'
    },
    conflict_columns=['counterparty_id'],
    update_columns=['counterparty_name', 'credit_rating']
)

# Close connections
connector.close()
```

### Context Manager

```python
with PostgreSQLConnector() as connector:
    # Use connector
    data = connector.execute_query_dict("SELECT * FROM portfolios")
# Connections automatically closed
```

### Repository Pattern

```python
from backend.connectors import PostgreSQLRepository

class UserRepository(PostgreSQLRepository):
    def get_by_username(self, username: str):
        query = "SELECT * FROM users WHERE username = %s"
        results = self.connector.execute_query_dict(query, (username,))
        return results[0] if results else None
    
    def create_user(self, user_data: dict):
        return self.connector.insert_one('users', user_data, returning='user_id')

# Usage
repo = UserRepository(connector)
user = repo.get_by_username('admin')
```

## Neo4j Connector

### Features

- Connection pooling with configurable parameters
- Read and write transaction support
- Node and relationship CRUD operations
- Path finding algorithms
- Graph algorithm integration (PageRank, community detection, etc.)
- Database statistics and monitoring

### Usage

```python
from backend.connectors import Neo4jConnector

# Initialize connector
connector = Neo4jConnector(
    uri='bolt://localhost:7687',
    user='neo4j',
    password='password',
    max_connection_pool_size=50
)

# Create node
portfolio = connector.create_node(
    labels=['Entity', 'Portfolio'],
    properties={
        'entity_id': 'portfolio_001',
        'name': 'Tech Portfolio',
        'risk_score': 0.65
    }
)

# Find nodes
portfolios = connector.find_nodes(
    labels=['Portfolio'],
    properties={'risk_score': 0.65},
    limit=10
)

# Create relationship
connector.create_relationship(
    from_node={'entity_id': 'portfolio_001'},
    to_node={'entity_id': 'CP001'},
    rel_type='TRANSACTS_WITH',
    properties={
        'transaction_count': 150,
        'total_volume': 25000000.00,
        'weight': 0.75
    }
)

# Find paths
paths = connector.find_paths(
    from_node={'entity_id': 'CP001'},
    to_node={'entity_id': 'portfolio_001'},
    rel_types=['PROPAGATES_TO', 'EXPOSED_TO'],
    max_depth=3
)

# Get neighbors
neighbors = connector.get_neighbors(
    node={'entity_id': 'portfolio_001'},
    rel_types=['CONTAINS', 'EXPOSED_TO'],
    direction='out',
    limit=100
)

# Update node
connector.update_node(
    'portfolio_001',
    {'risk_score': 0.70, 'status': 'active'}
)

# Close connection
connector.close()
```

### Context Manager

```python
with Neo4jConnector() as connector:
    # Use connector
    nodes = connector.find_nodes(labels=['Portfolio'])
# Connection automatically closed
```

### Repository Pattern

```python
from backend.connectors import Neo4jRepository

class PortfolioRepository(Neo4jRepository):
    def get_portfolio_network(self, portfolio_id: str):
        query = """
            MATCH (p:Portfolio {entity_id: $portfolio_id})-[r]-(connected)
            RETURN p, r, connected
        """
        return self.connector.execute_read(query, {'portfolio_id': portfolio_id})
    
    def calculate_risk_propagation(self, portfolio_id: str):
        query = """
            MATCH path = (p:Portfolio {entity_id: $portfolio_id})-[:PROPAGATES_TO*1..3]->(target)
            RETURN path, length(path) as depth
            ORDER BY depth
        """
        return self.connector.execute_read(query, {'portfolio_id': portfolio_id})

# Usage
repo = PortfolioRepository(connector)
network = repo.get_portfolio_network('portfolio_001')
```

## Data Ingestion Service

The `DataIngestionService` combines both connectors to provide high-level data ingestion capabilities.

### Features

- Validates and cleans incoming data
- Inserts data into PostgreSQL
- Creates/updates corresponding graph structures in Neo4j
- Batch processing for large datasets
- Error handling and reporting

### Usage

```python
from backend.services import DataIngestionService
from backend.connectors import PostgreSQLConnector, Neo4jConnector

# Initialize connectors
pg_connector = PostgreSQLConnector()
neo4j_connector = Neo4jConnector()

# Initialize service
service = DataIngestionService(
    pg_connector=pg_connector,
    neo4j_connector=neo4j_connector,
    batch_size=1000,
    max_workers=4
)

# Ingest market data
result = service.ingest_market_data([
    {
        'asset_id': 'AAPL',
        'timestamp': datetime.now(),
        'close_price': 175.50,
        'volume': 1000000
    }
])
print(f"Ingested {result['successful']} records")

# Ingest transactions
result = service.ingest_transactions([
    {
        'portfolio_id': 'portfolio_001',
        'asset_id': 'AAPL',
        'quantity': 100,
        'price': 175.50,
        'transaction_date': datetime.now(),
        'counterparty_id': 'CP001'
    }
])

# Ingest risk calculations
result = service.ingest_risk_calculations([
    {
        'entity_id': 'portfolio_001',
        'entity_type': 'portfolio',
        'calculation_type': 'var',
        'risk_score': 0.65,
        'var_95': 50000.00,
        'var_99': 75000.00
    }
])

# Close service
service.close()
```

## Configuration

### Environment Variables

```bash
# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=risk_constellation
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Neo4j
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
```

### Connection Pool Settings

**PostgreSQL:**
- `min_connections`: Minimum connections in pool (default: 1)
- `max_connections`: Maximum connections in pool (default: 10)

**Neo4j:**
- `max_connection_lifetime`: Maximum connection lifetime in seconds (default: 3600)
- `max_connection_pool_size`: Maximum connections in pool (default: 50)
- `connection_acquisition_timeout`: Timeout for acquiring connection (default: 60)

## Error Handling

All connectors implement proper error handling:

```python
try:
    connector = PostgreSQLConnector()
    data = connector.execute_query_dict("SELECT * FROM users")
except Exception as e:
    logger.error(f"Database error: {e}")
    # Handle error
finally:
    connector.close()
```

## Testing

### Test PostgreSQL Connection

```python
connector = PostgreSQLConnector()
if connector.test_connection():
    print("✓ PostgreSQL connection successful")
else:
    print("✗ PostgreSQL connection failed")
connector.close()
```

### Test Neo4j Connection

```python
connector = Neo4jConnector()
if connector.test_connection():
    print("✓ Neo4j connection successful")
else:
    print("✗ Neo4j connection failed")
connector.close()
```

## Performance Considerations

### PostgreSQL

- Use `bulk_insert()` for large datasets (batches of 1000 records)
- Use `execute_many()` for multiple similar queries
- Use connection pooling to avoid connection overhead
- Use indexes on frequently queried columns
- Use `EXPLAIN ANALYZE` to optimize queries

### Neo4j

- Use parameterized queries to enable query caching
- Create indexes on frequently queried properties
- Use `PROFILE` to analyze query performance
- Batch node/relationship creation for large imports
- Use read transactions for queries, write transactions for updates

## Best Practices

1. **Always close connections**: Use context managers or explicit `close()` calls
2. **Use connection pooling**: Don't create new connections for each query
3. **Parameterize queries**: Prevent SQL injection and enable query caching
4. **Handle errors gracefully**: Implement proper try/except blocks
5. **Log operations**: Use logging for debugging and monitoring
6. **Validate data**: Clean and validate data before insertion
7. **Use transactions**: Group related operations in transactions
8. **Monitor performance**: Track query execution times and connection pool usage

## Troubleshooting

### PostgreSQL Issues

**Connection refused:**
- Check if PostgreSQL is running: `docker ps | grep postgres`
- Verify connection parameters
- Check firewall settings

**Too many connections:**
- Increase `max_connections` in PostgreSQL config
- Reduce connection pool size
- Ensure connections are properly closed

### Neo4j Issues

**Authentication failed:**
- Verify username and password
- Check if Neo4j is running: `docker ps | grep neo4j`
- Reset password if needed

**Query timeout:**
- Increase `connection_acquisition_timeout`
- Optimize query with indexes
- Use `PROFILE` to identify bottlenecks

## Dependencies

```bash
pip install psycopg2-binary  # PostgreSQL driver
pip install neo4j            # Neo4j driver
```

## Next Steps

After setting up connectors:
1. Create repository classes for each entity type
2. Implement caching layer (Redis)
3. Build FastAPI endpoints
4. Add authentication and authorization
5. Implement real-time updates with WebSockets