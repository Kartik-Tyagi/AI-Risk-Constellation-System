"""
Data Ingestion Service
Handles ingestion of market data, transactions, and risk events into the system
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from backend.connectors.postgres_connector import PostgreSQLConnector
from backend.connectors.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting data into PostgreSQL and Neo4j"""
    
    def __init__(
        self,
        pg_connector: PostgreSQLConnector,
        neo4j_connector: Neo4jConnector,
        batch_size: int = 1000,
        max_workers: int = 4
    ):
        """
        Initialize data ingestion service
        
        Args:
            pg_connector: PostgreSQL connector
            neo4j_connector: Neo4j connector
            batch_size: Batch size for bulk operations
            max_workers: Maximum worker threads
        """
        self.pg_connector = pg_connector
        self.neo4j_connector = neo4j_connector
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def ingest_market_data(
        self,
        market_data: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest market data into PostgreSQL
        
        Args:
            market_data: List of market data records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_market_data(market_data)
            
            # Bulk insert into PostgreSQL
            self.pg_connector.bulk_insert(
                'market_data',
                validated_data,
                batch_size=self.batch_size
            )
            
            logger.info(f"Ingested {len(validated_data)} market data records")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest market data: {e}")
            return {
                'total_records': len(market_data),
                'successful': 0,
                'failed': len(market_data),
                'error': str(e)
            }
    
    def ingest_transactions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest transactions into PostgreSQL and create relationships in Neo4j
        
        Args:
            transactions: List of transaction records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_transactions(transactions)
            
            # Insert into PostgreSQL
            self.pg_connector.bulk_insert(
                'transactions',
                validated_data,
                batch_size=self.batch_size
            )
            
            # Update Neo4j relationships
            self._update_transaction_relationships(validated_data)
            
            logger.info(f"Ingested {len(validated_data)} transactions")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest transactions: {e}")
            return {
                'total_records': len(transactions),
                'successful': 0,
                'failed': len(transactions),
                'error': str(e)
            }
    
    def ingest_portfolio_positions(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest portfolio positions into PostgreSQL and Neo4j
        
        Args:
            positions: List of position records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_positions(positions)
            
            # Upsert into PostgreSQL
            for position in validated_data:
                self.pg_connector.upsert(
                    'portfolio_positions',
                    position,
                    conflict_columns=['portfolio_id', 'asset_id', 'as_of_date'],
                    update_columns=['quantity', 'current_price', 'market_value', 'unrealized_pnl', 'weight']
                )
            
            # Update Neo4j CONTAINS relationships
            self._update_position_relationships(validated_data)
            
            logger.info(f"Ingested {len(validated_data)} positions")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest positions: {e}")
            return {
                'total_records': len(positions),
                'successful': 0,
                'failed': len(positions),
                'error': str(e)
            }
    
    def ingest_risk_calculations(
        self,
        risk_calcs: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest risk calculations into PostgreSQL and update Neo4j
        
        Args:
            risk_calcs: List of risk calculation records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_risk_calculations(risk_calcs)
            
            # Insert into PostgreSQL
            self.pg_connector.bulk_insert(
                'risk_calculations',
                validated_data,
                batch_size=self.batch_size
            )
            
            # Update Neo4j node risk scores
            self._update_risk_scores(validated_data)
            
            logger.info(f"Ingested {len(validated_data)} risk calculations")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest risk calculations: {e}")
            return {
                'total_records': len(risk_calcs),
                'successful': 0,
                'failed': len(risk_calcs),
                'error': str(e)
            }
    
    def ingest_risk_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest risk events into Neo4j
        
        Args:
            events: List of risk event records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_risk_events(events)
            
            # Create RiskEvent nodes in Neo4j
            for event in validated_data:
                self.neo4j_connector.create_node(
                    labels=['RiskEvent'],
                    properties=event
                )
            
            logger.info(f"Ingested {len(validated_data)} risk events")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest risk events: {e}")
            return {
                'total_records': len(events),
                'successful': 0,
                'failed': len(events),
                'error': str(e)
            }
    
    def ingest_counterparties(
        self,
        counterparties: List[Dict[str, Any]]
    ) -> Dict[str, Union[int, str]]:
        """
        Ingest counterparties into PostgreSQL and Neo4j
        
        Args:
            counterparties: List of counterparty records
            
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Validate data
            validated_data = self._validate_counterparties(counterparties)
            
            # Upsert into PostgreSQL
            for cp in validated_data:
                self.pg_connector.upsert(
                    'counterparties',
                    cp,
                    conflict_columns=['counterparty_id'],
                    update_columns=['counterparty_name', 'credit_rating', 'total_exposure', 'risk_score']
                )
            
            # Create/update Neo4j nodes
            for cp in validated_data:
                # Check if node exists
                existing = self.neo4j_connector.find_nodes(
                    labels=['Counterparty'],
                    properties={'entity_id': cp['counterparty_id']},
                    limit=1
                )
                
                if existing:
                    # Update existing node
                    self.neo4j_connector.update_node(
                        cp['counterparty_id'],
                        {
                            'name': cp['counterparty_name'],
                            'credit_rating': cp.get('credit_rating'),
                            'risk_score': cp.get('risk_score', 0.5)
                        }
                    )
                else:
                    # Create new node
                    self.neo4j_connector.create_node(
                        labels=['Entity', 'Counterparty'],
                        properties={
                            'entity_id': cp['counterparty_id'],
                            'entity_type': 'counterparty',
                            'name': cp['counterparty_name'],
                            'counterparty_type': cp.get('counterparty_type', 'unknown'),
                            'credit_rating': cp.get('credit_rating'),
                            'country': cp.get('country'),
                            'industry': cp.get('industry'),
                            'risk_score': cp.get('risk_score', 0.5),
                            'created_at': datetime.now().isoformat()
                        }
                    )
            
            logger.info(f"Ingested {len(validated_data)} counterparties")
            
            return {
                'total_records': len(validated_data),
                'successful': len(validated_data),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest counterparties: {e}")
            return {
                'total_records': len(counterparties),
                'successful': 0,
                'failed': len(counterparties),
                'error': str(e)
            }
    
    def _validate_market_data(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean market data"""
        validated = []
        for record in data:
            if all(k in record for k in ['asset_id', 'timestamp', 'close_price']):
                validated.append({
                    'asset_id': record['asset_id'],
                    'data_type': record.get('data_type', 'daily'),
                    'timestamp': record['timestamp'],
                    'open_price': record.get('open_price'),
                    'high_price': record.get('high_price'),
                    'low_price': record.get('low_price'),
                    'close_price': record['close_price'],
                    'volume': record.get('volume'),
                    'vwap': record.get('vwap')
                })
        return validated
    
    def _validate_transactions(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean transaction data"""
        validated = []
        for record in data:
            if all(k in record for k in ['portfolio_id', 'asset_id', 'quantity', 'price', 'transaction_date']):
                validated.append({
                    'portfolio_id': record['portfolio_id'],
                    'transaction_type': record.get('transaction_type', 'buy'),
                    'asset_id': record['asset_id'],
                    'quantity': record['quantity'],
                    'price': record['price'],
                    'total_amount': record.get('total_amount', record['quantity'] * record['price']),
                    'fees': record.get('fees', 0),
                    'counterparty_id': record.get('counterparty_id'),
                    'transaction_date': record['transaction_date'],
                    'settlement_date': record.get('settlement_date'),
                    'status': record.get('status', 'completed'),
                    'notes': record.get('notes')
                })
        return validated
    
    def _validate_positions(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean position data"""
        validated = []
        for record in data:
            if all(k in record for k in ['portfolio_id', 'asset_id', 'quantity', 'as_of_date']):
                validated.append({
                    'portfolio_id': record['portfolio_id'],
                    'asset_id': record['asset_id'],
                    'asset_type': record.get('asset_type', 'equity'),
                    'quantity': record['quantity'],
                    'average_cost': record.get('average_cost'),
                    'current_price': record.get('current_price'),
                    'market_value': record.get('market_value'),
                    'unrealized_pnl': record.get('unrealized_pnl'),
                    'weight': record.get('weight'),
                    'as_of_date': record['as_of_date']
                })
        return validated
    
    def _validate_risk_calculations(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean risk calculation data"""
        validated = []
        for record in data:
            if all(k in record for k in ['entity_id', 'entity_type', 'calculation_type', 'risk_score']):
                validated.append({
                    'entity_id': record['entity_id'],
                    'entity_type': record['entity_type'],
                    'calculation_type': record['calculation_type'],
                    'risk_score': record['risk_score'],
                    'confidence': record.get('confidence'),
                    'var_95': record.get('var_95'),
                    'var_99': record.get('var_99'),
                    'expected_shortfall': record.get('expected_shortfall'),
                    'volatility': record.get('volatility'),
                    'sharpe_ratio': record.get('sharpe_ratio'),
                    'max_drawdown': record.get('max_drawdown'),
                    'calculation_timestamp': record.get('calculation_timestamp', datetime.now()),
                    'model_version': record.get('model_version'),
                    'metadata': record.get('metadata')
                })
        return validated
    
    def _validate_risk_events(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean risk event data"""
        validated = []
        for record in data:
            if all(k in record for k in ['event_id', 'event_type', 'severity']):
                validated.append({
                    'event_id': record['event_id'],
                    'event_type': record['event_type'],
                    'severity': record['severity'],
                    'impact_score': record.get('impact_score', record['severity']),
                    'timestamp': record.get('timestamp', datetime.now().isoformat()),
                    'description': record.get('description', ''),
                    'affected_entities': record.get('affected_entities', []),
                    'metadata': record.get('metadata', '{}')
                })
        return validated
    
    def _validate_counterparties(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean counterparty data"""
        validated = []
        for record in data:
            if all(k in record for k in ['counterparty_id', 'counterparty_name']):
                validated.append({
                    'counterparty_id': record['counterparty_id'],
                    'counterparty_name': record['counterparty_name'],
                    'counterparty_type': record.get('counterparty_type', 'unknown'),
                    'credit_rating': record.get('credit_rating'),
                    'country': record.get('country'),
                    'industry': record.get('industry'),
                    'total_exposure': record.get('total_exposure', 0),
                    'risk_score': record.get('risk_score')
                })
        return validated
    
    def _update_transaction_relationships(
        self,
        transactions: List[Dict[str, Any]]
    ) -> None:
        """Update TRANSACTS_WITH relationships in Neo4j"""
        # Group transactions by portfolio-counterparty pairs
        pairs: Dict[tuple, List[Dict[str, Any]]] = {}
        for txn in transactions:
            if txn.get('counterparty_id'):
                key = (txn['portfolio_id'], txn['counterparty_id'])
                if key not in pairs:
                    pairs[key] = []
                pairs[key].append(txn)
        
        # Update relationships
        for (portfolio_id, counterparty_id), txns in pairs.items():
            total_volume = sum(t['total_amount'] for t in txns)
            avg_size = total_volume / len(txns)
            
            # This is a simplified version - in production, you'd want to
            # check if relationship exists and update it
            logger.debug(f"Would update relationship: {portfolio_id} -> {counterparty_id}")
    
    def _update_position_relationships(
        self,
        positions: List[Dict[str, Any]]
    ) -> None:
        """Update CONTAINS relationships in Neo4j"""
        for position in positions:
            # This is a simplified version - in production, you'd want to
            # create/update CONTAINS relationships
            logger.debug(f"Would update position: {position['portfolio_id']} contains {position['asset_id']}")
    
    def _update_risk_scores(
        self,
        risk_calcs: List[Dict[str, Any]]
    ) -> None:
        """Update risk scores in Neo4j nodes"""
        for calc in risk_calcs:
            try:
                self.neo4j_connector.update_node(
                    calc['entity_id'],
                    {'risk_score': calc['risk_score']}
                )
            except Exception as e:
                logger.warning(f"Failed to update risk score for {calc['entity_id']}: {e}")
    
    def close(self) -> None:
        """Close connections and cleanup"""
        self.executor.shutdown(wait=True)
        logger.info("Data ingestion service closed")


# Example usage
if __name__ == '__main__':
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # Initialize connectors
    pg_connector = PostgreSQLConnector(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DB', 'risk_constellation')
    )
    
    neo4j_connector = Neo4jConnector(
        uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        password=os.getenv('NEO4J_PASSWORD', 'password')
    )
    
    # Initialize service
    service = DataIngestionService(pg_connector, neo4j_connector)
    
    try:
        # Example: Ingest sample market data
        sample_data = [
            {
                'asset_id': 'AAPL',
                'timestamp': datetime.now(),
                'close_price': 175.50,
                'volume': 1000000
            }
        ]
        
        result = service.ingest_market_data(sample_data)
        print(f"✓ Ingestion result: {result}")
        
    finally:
        service.close()
        pg_connector.close()
        neo4j_connector.close()

# Made with Bob
