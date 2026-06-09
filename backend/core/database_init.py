"""
Database Initialization Script
Initializes PostgreSQL and Neo4j databases with schemas and sample data
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
import json

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    ISOLATION_LEVEL_AUTOCOMMIT = None  # type: ignore
    if TYPE_CHECKING:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    if TYPE_CHECKING:
        from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Initialize and configure databases"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize database connections
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config or self._load_default_config()
        self.pg_conn: Optional[Any] = None
        self.neo4j_driver: Optional[Any] = None
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default database configuration"""
        return {
            'postgres': {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'database': os.getenv('POSTGRES_DB', 'risk_constellation'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
            },
            'neo4j': {
                'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                'user': os.getenv('NEO4J_USER', 'neo4j'),
                'password': os.getenv('NEO4J_PASSWORD', 'password')
            }
        }
    
    def connect_postgres(self) -> None:
        """Establish PostgreSQL connection"""
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is not installed")
            
        try:
            pg_config = self.config['postgres']
            self.pg_conn = psycopg2.connect(
                host=pg_config['host'],
                port=pg_config['port'],
                database=pg_config['database'],
                user=pg_config['user'],
                password=pg_config['password']
            )
            if self.pg_conn:
                self.pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Connected to PostgreSQL successfully")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def connect_neo4j(self) -> None:
        """Establish Neo4j connection"""
        if not NEO4J_AVAILABLE:
            raise RuntimeError("neo4j driver is not installed")
            
        try:
            neo4j_config = self.config['neo4j']
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            # Test connection
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def initialize_postgres_schema(self) -> None:
        """Initialize PostgreSQL schema"""
        if not self.pg_conn:
            raise RuntimeError("PostgreSQL connection not established")
            
        try:
            schema_path = os.path.join(
                os.path.dirname(__file__),
                'postgres_schema.sql'
            )
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            cursor = self.pg_conn.cursor()
            cursor.execute(schema_sql)
            cursor.close()
            
            logger.info("PostgreSQL schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise
    
    def initialize_neo4j_schema(self) -> None:
        """Initialize Neo4j schema"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j connection not established")
            
        try:
            schema_path = os.path.join(
                os.path.dirname(__file__),
                'neo4j_schema.cypher'
            )
            
            with open(schema_path, 'r') as f:
                schema_cypher = f.read()
            
            # Split by semicolons and execute each statement
            statements = [
                stmt.strip()
                for stmt in schema_cypher.split(';')
                if stmt.strip() and not stmt.strip().startswith('//')
            ]
            
            with self.neo4j_driver.session() as session:
                for statement in statements:
                    if statement:
                        try:
                            session.run(statement)
                        except Exception as e:
                            # Some statements might fail if already exist
                            logger.debug(f"Statement execution note: {e}")
            
            logger.info("Neo4j schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
            raise
    
    def load_sample_data_postgres(self) -> None:
        """Load sample data into PostgreSQL"""
        if not self.pg_conn:
            raise RuntimeError("PostgreSQL connection not established")
            
        try:
            cursor = self.pg_conn.cursor()
            
            # Create sample user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES ('admin', 'admin@example.com', 'hashed_password', 'Admin User', 'admin')
                ON CONFLICT (username) DO NOTHING
                RETURNING user_id
            """)
            result = cursor.fetchone()
            user_id = result[0] if result else None
            
            # Create sample portfolio
            if user_id:
                cursor.execute("""
                    INSERT INTO portfolios (
                        portfolio_name, portfolio_type, owner_id, 
                        total_value, inception_date
                    )
                    VALUES (
                        'Tech Growth Portfolio', 'equity', %s,
                        10000000.00, '2020-01-01'
                    )
                    ON CONFLICT DO NOTHING
                    RETURNING portfolio_id
                """, (user_id,))
                result = cursor.fetchone()
                portfolio_id = result[0] if result else None
            
            # Create sample counterparties
            counterparties = [
                ('CP001', 'Global Bank Corp', 'bank', 'AA', 'USA', 'Financial Services'),
                ('CP002', 'Tech Ventures LLC', 'hedge_fund', 'A', 'USA', 'Technology'),
                ('CP003', 'Energy Holdings Inc', 'corporation', 'BBB', 'USA', 'Energy')
            ]
            
            for cp_id, name, cp_type, rating, country, industry in counterparties:
                cursor.execute("""
                    INSERT INTO counterparties (
                        counterparty_id, counterparty_name, counterparty_type,
                        credit_rating, country, industry
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (counterparty_id) DO NOTHING
                """, (cp_id, name, cp_type, rating, country, industry))
            
            # Create sample market data
            assets = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            base_date = datetime.now() - timedelta(days=30)
            
            for i in range(30):
                date = base_date + timedelta(days=i)
                for asset in assets:
                    cursor.execute("""
                        INSERT INTO market_data (
                            asset_id, data_type, timestamp,
                            open_price, high_price, low_price, close_price, volume
                        )
                        VALUES (%s, 'daily', %s, %s, %s, %s, %s, %s)
                    """, (
                        asset, date,
                        150.0 + i, 155.0 + i, 148.0 + i, 152.0 + i,
                        1000000 + i * 10000
                    ))
            
            cursor.close()
            logger.info("Sample data loaded into PostgreSQL successfully")
        except Exception as e:
            logger.error(f"Failed to load sample data into PostgreSQL: {e}")
            raise
    
    def load_sample_data_neo4j(self) -> None:
        """Load sample data into Neo4j"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j connection not established")
            
        try:
            with self.neo4j_driver.session() as session:
                # Create sample portfolios
                session.run("""
                    CREATE (p:Entity:Portfolio {
                        entity_id: 'portfolio_001',
                        entity_type: 'portfolio',
                        name: 'Tech Growth Portfolio',
                        risk_score: 0.65,
                        portfolio_type: 'equity',
                        total_value: 10000000.00,
                        currency: 'USD',
                        num_positions: 25,
                        inception_date: date('2020-01-01'),
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                """)
                
                # Create sample counterparties
                counterparties = [
                    {
                        'id': 'CP001',
                        'name': 'Global Bank Corp',
                        'type': 'bank',
                        'rating': 'AA',
                        'country': 'USA',
                        'industry': 'Financial Services',
                        'risk_score': 0.35
                    },
                    {
                        'id': 'CP002',
                        'name': 'Tech Ventures LLC',
                        'type': 'hedge_fund',
                        'rating': 'A',
                        'country': 'USA',
                        'industry': 'Technology',
                        'risk_score': 0.45
                    }
                ]
                
                for cp in counterparties:
                    session.run("""
                        CREATE (c:Entity:Counterparty {
                            entity_id: $id,
                            entity_type: 'counterparty',
                            name: $name,
                            risk_score: $risk_score,
                            counterparty_type: $type,
                            credit_rating: $rating,
                            country: $country,
                            industry: $industry,
                            total_exposure: 5000000.00,
                            created_at: datetime(),
                            updated_at: datetime()
                        })
                    """, cp)
                
                # Create sample assets
                assets = [
                    {'id': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'price': 175.50},
                    {'id': 'MSFT', 'name': 'Microsoft Corp.', 'sector': 'Technology', 'price': 380.25},
                    {'id': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'price': 140.75}
                ]
                
                for asset in assets:
                    session.run("""
                        CREATE (a:Entity:Asset {
                            entity_id: $id,
                            entity_type: 'asset',
                            name: $name,
                            risk_score: 0.45,
                            asset_type: 'equity',
                            ticker: $id,
                            sector: $sector,
                            current_price: $price,
                            volatility: 0.25,
                            created_at: datetime(),
                            updated_at: datetime()
                        })
                    """, asset)
                
                # Create relationships
                session.run("""
                    MATCH (p:Portfolio {entity_id: 'portfolio_001'})
                    MATCH (c:Counterparty {entity_id: 'CP001'})
                    CREATE (p)-[r:TRANSACTS_WITH {
                        transaction_count: 150,
                        total_volume: 25000000.00,
                        avg_transaction_size: 166666.67,
                        weight: 0.75,
                        first_transaction: date('2020-01-15'),
                        last_transaction: date('2024-06-01'),
                        risk_contribution: 0.45
                    }]->(c)
                """)
                
                session.run("""
                    MATCH (p:Portfolio {entity_id: 'portfolio_001'})
                    MATCH (c:Counterparty {entity_id: 'CP001'})
                    CREATE (p)-[r:EXPOSED_TO {
                        exposure_type: 'credit',
                        exposure_amount: 5000000.00,
                        exposure_percentage: 0.50,
                        timestamp: datetime(),
                        confidence: 0.90,
                        risk_score: 0.35
                    }]->(c)
                """)
                
                session.run("""
                    MATCH (p:Portfolio {entity_id: 'portfolio_001'})
                    MATCH (a:Asset {entity_id: 'AAPL'})
                    CREATE (p)-[r:CONTAINS {
                        quantity: 10000,
                        weight: 0.175,
                        cost_basis: 150.00,
                        market_value: 1755000.00,
                        unrealized_pnl: 255000.00,
                        timestamp: datetime()
                    }]->(a)
                """)
                
                session.run("""
                    MATCH (a1:Asset {entity_id: 'AAPL'})
                    MATCH (a2:Asset {entity_id: 'MSFT'})
                    CREATE (a1)-[r:CORRELATES_WITH {
                        correlation_coefficient: 0.85,
                        correlation_type: 'price',
                        lookback_period: 252,
                        timestamp: datetime(),
                        significance: 0.001
                    }]->(a2)
                """)
                
                session.run("""
                    MATCH (c:Counterparty {entity_id: 'CP001'})
                    MATCH (p:Portfolio {entity_id: 'portfolio_001'})
                    CREATE (c)-[r:PROPAGATES_TO {
                        propagation_probability: 0.65,
                        propagation_delay: 24,
                        amplification_factor: 1.25,
                        path_strength: 0.70,
                        timestamp: datetime(),
                        historical_events: 5
                    }]->(p)
                """)
                
                # Create sample risk event
                session.run("""
                    CREATE (r:RiskEvent {
                        event_id: 'event_001',
                        event_type: 'market_shock',
                        severity: 0.85,
                        impact_score: 0.75,
                        timestamp: datetime(),
                        description: 'Sudden market volatility spike',
                        affected_entities: ['portfolio_001', 'AAPL'],
                        metadata: '{}'
                    })
                """)
                
                # Create sample market condition
                session.run("""
                    CREATE (m:MarketCondition {
                        condition_id: 'condition_001',
                        condition_type: 'volatility',
                        indicator_name: 'VIX',
                        value: 28.5,
                        timestamp: datetime(),
                        regime: 'volatile',
                        metadata: '{}'
                    })
                """)
            
            logger.info("Sample data loaded into Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to load sample data into Neo4j: {e}")
            raise
    
    def verify_connections(self) -> Dict[str, bool]:
        """Verify database connections and data"""
        results = {
            'postgres_connected': False,
            'neo4j_connected': False,
            'postgres_data': False,
            'neo4j_data': False
        }
        
        # Verify PostgreSQL
        try:
            if not self.pg_conn:
                raise RuntimeError("PostgreSQL connection not established")
                
            cursor = self.pg_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            count = result[0] if result else 0
            results['postgres_connected'] = True
            results['postgres_data'] = count > 0
            cursor.close()
            logger.info(f"PostgreSQL verification: {count} users found")
        except Exception as e:
            logger.error(f"PostgreSQL verification failed: {e}")
        
        # Verify Neo4j
        try:
            if not self.neo4j_driver:
                raise RuntimeError("Neo4j connection not established")
                
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()['count']
                results['neo4j_connected'] = True
                results['neo4j_data'] = count > 0
                logger.info(f"Neo4j verification: {count} nodes found")
        except Exception as e:
            logger.error(f"Neo4j verification failed: {e}")
        
        return results
    
    def close_connections(self) -> None:
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("PostgreSQL connection closed")
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Neo4j connection closed")
    
    def initialize_all(self, load_sample_data: bool = True) -> None:
        """
        Initialize all databases
        
        Args:
            load_sample_data: Whether to load sample data
        """
        try:
            logger.info("Starting database initialization...")
            
            # Connect to databases
            self.connect_postgres()
            self.connect_neo4j()
            
            # Initialize schemas
            logger.info("Initializing PostgreSQL schema...")
            self.initialize_postgres_schema()
            
            logger.info("Initializing Neo4j schema...")
            self.initialize_neo4j_schema()
            
            # Load sample data if requested
            if load_sample_data:
                logger.info("Loading sample data into PostgreSQL...")
                self.load_sample_data_postgres()
                
                logger.info("Loading sample data into Neo4j...")
                self.load_sample_data_neo4j()
            
            # Verify everything
            logger.info("Verifying database setup...")
            results = self.verify_connections()
            
            logger.info("Database initialization complete!")
            logger.info(f"Verification results: {json.dumps(results, indent=2)}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            self.close_connections()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize databases')
    parser.add_argument(
        '--no-sample-data',
        action='store_true',
        help='Skip loading sample data'
    )
    args = parser.parse_args()
    
    initializer = DatabaseInitializer()
    initializer.initialize_all(load_sample_data=not args.no_sample_data)


if __name__ == '__main__':
    main()

# Made with Bob
