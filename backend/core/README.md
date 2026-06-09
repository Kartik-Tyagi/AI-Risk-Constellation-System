# Database Core Module

This module contains database schemas, initialization scripts, and migration tools for the AI Risk Constellation System.

## Overview

The system uses two databases:
- **PostgreSQL**: Relational database for structured data (portfolios, transactions, market data, risk calculations)
- **Neo4j**: Graph database for entity relationships and risk propagation networks

## Files

### Schema Files

- `postgres_schema.sql`: Complete PostgreSQL schema with tables, indexes, triggers, and views
- `neo4j_schema.cypher`: Neo4j schema with node types, relationship types, constraints, and indexes

### Initialization

- `database_init.py`: Python script to initialize both databases with schemas and sample data

### Migrations

- `migrations/`: Directory for database migration scripts
  - `001_initial_schema.sql`: Initial schema migration

## Database Setup

### Prerequisites

1. Docker and Docker Compose installed
2. Python 3.11+ with required packages:
   ```bash
   pip install psycopg2-binary neo4j
   ```

### Starting Databases

From the project root directory:

```bash
docker-compose up -d postgres neo4j
```

This starts:
- PostgreSQL on port 5432
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)

### Initializing Databases

Run the initialization script:

```bash
python backend/core/database_init.py
```

To skip loading sample data:

```bash
python backend/core/database_init.py --no-sample-data
```

### Verifying Setup

The initialization script automatically verifies:
- Database connections
- Schema creation
- Sample data loading (if enabled)

You can also manually verify:

**PostgreSQL:**
```bash
docker exec -it postgres psql -U postgres -d risk_constellation -c "SELECT COUNT(*) FROM users;"
```

**Neo4j:**
- Open browser to http://localhost:7474
- Login with username: `neo4j`, password: `password`
- Run query: `MATCH (n) RETURN count(n)`

## PostgreSQL Schema

### Main Tables

- **users**: System users and authentication
- **portfolios**: Investment portfolios
- **portfolio_positions**: Current positions within portfolios
- **transactions**: Historical transaction records
- **counterparties**: Counterparty entities and risk profiles
- **market_data**: Historical market price and volume data
- **market_indicators**: Market indicators (VIX, etc.)
- **risk_calculations**: Risk calculation results
- **risk_dna**: Risk DNA fingerprints
- **risk_alerts**: Risk alerts and notifications
- **model_metadata**: ML model versions and metadata
- **audit_log**: System audit trail

### Key Features

- UUID primary keys for distributed systems
- Automatic `updated_at` timestamp triggers
- Comprehensive indexes for query performance
- JSONB columns for flexible metadata
- Views for common queries
- Foreign key constraints with cascading deletes

## Neo4j Schema

### Node Types

- **Entity** (base type)
  - **Portfolio**: Investment portfolios
  - **Counterparty**: Counterparty entities
  - **Asset**: Financial assets
- **RiskEvent**: Risk events and incidents
- **MarketCondition**: Market conditions and regimes

### Relationship Types

- **TRANSACTS_WITH**: Transactional relationships
- **EXPOSED_TO**: Risk exposure relationships
- **CORRELATES_WITH**: Correlation between entities
- **PROPAGATES_TO**: Risk propagation paths
- **CONTAINS**: Containment (portfolio contains assets)
- **TRIGGERS**: Event triggering relationships
- **AFFECTS**: Market condition impacts

### Key Features

- Unique constraints on entity IDs
- Indexes on frequently queried properties
- Weighted relationships for network analysis
- Temporal properties for time-series analysis
- Support for graph algorithms (PageRank, community detection, shortest path)

## Sample Data

The initialization script loads sample data including:

**PostgreSQL:**
- 1 admin user
- 1 sample portfolio
- 3 counterparties
- 5 assets with 30 days of market data

**Neo4j:**
- 1 portfolio node
- 2 counterparty nodes
- 3 asset nodes
- Multiple relationship types demonstrating the graph structure
- 1 risk event
- 1 market condition

## Migrations

### Creating a New Migration

1. Create a new SQL file in `migrations/` with sequential numbering:
   ```
   migrations/002_add_new_feature.sql
   ```

2. Include migration tracking:
   ```sql
   -- Migration: 002_add_new_feature
   -- Description: Add new feature tables
   -- Date: YYYY-MM-DD
   
   -- Your schema changes here
   
   -- Record migration
   INSERT INTO schema_migrations (migration_name, description)
   VALUES ('002_add_new_feature', 'Add new feature tables')
   ON CONFLICT (migration_name) DO NOTHING;
   ```

3. Apply migration:
   ```bash
   psql -U postgres -d risk_constellation -f backend/core/migrations/002_add_new_feature.sql
   ```

## Environment Variables

Configure database connections using environment variables:

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

## Troubleshooting

### PostgreSQL Connection Issues

1. Check if container is running:
   ```bash
   docker ps | grep postgres
   ```

2. Check logs:
   ```bash
   docker logs postgres
   ```

3. Verify connection:
   ```bash
   docker exec -it postgres psql -U postgres -c "SELECT version();"
   ```

### Neo4j Connection Issues

1. Check if container is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Check logs:
   ```bash
   docker logs neo4j
   ```

3. Access Neo4j Browser:
   - URL: http://localhost:7474
   - Default credentials: neo4j/password

### Schema Issues

If schema initialization fails:

1. Drop and recreate databases:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

2. Re-run initialization:
   ```bash
   python backend/core/database_init.py
   ```

## Performance Considerations

### PostgreSQL

- Indexes are created on frequently queried columns
- Partitioning can be added for large tables (market_data, transactions)
- Connection pooling recommended for production (use pgBouncer)
- Regular VACUUM and ANALYZE for query optimization

### Neo4j

- Constraints and indexes improve query performance
- Use EXPLAIN and PROFILE for query optimization
- Consider graph projections for complex algorithms
- Monitor memory usage for large graphs

## Security

### Development (Current Setup)

- Default passwords (change for production)
- No SSL/TLS (local only)
- No network restrictions

### Production Recommendations

- Use strong passwords
- Enable SSL/TLS for all connections
- Implement network segmentation
- Use connection pooling with authentication
- Regular security audits
- Encrypted backups

## Backup and Recovery

### PostgreSQL Backup

```bash
docker exec postgres pg_dump -U postgres risk_constellation > backup.sql
```

### PostgreSQL Restore

```bash
docker exec -i postgres psql -U postgres risk_constellation < backup.sql
```

### Neo4j Backup

```bash
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump
```

### Neo4j Restore

```bash
docker exec neo4j neo4j-admin load --from=/backups/neo4j-backup.dump --database=neo4j --force
```

## Next Steps

After database setup:

1. Proceed to Step 2.2: Implement Database Connectors
2. Create data access layer (DAL)
3. Implement repository pattern for data operations
4. Add caching layer (Redis)
5. Implement API endpoints

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)