"""
Graph Builder Service
Builds and updates Neo4j graph from relational data
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.connectors.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)


class GraphBuilderService:
    """Service for building and updating Neo4j graph"""
    
    def __init__(self, neo4j_connector: Neo4jConnector):
        """
        Initialize graph builder
        
        Args:
            neo4j_connector: Neo4j connector instance
        """
        self.connector = neo4j_connector
    
    def build_portfolio_node(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update portfolio node"""
        node_properties = {
            'entity_id': portfolio_data['portfolio_id'],
            'entity_type': 'portfolio',
            'name': portfolio_data['portfolio_name'],
            'portfolio_type': portfolio_data.get('portfolio_type', 'unknown'),
            'total_value': portfolio_data.get('total_value', 0),
            'currency': portfolio_data.get('currency', 'USD'),
            'risk_score': portfolio_data.get('risk_score', 0.5),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Check if exists
        existing = self.connector.find_nodes(
            labels=['Portfolio'],
            properties={'entity_id': node_properties['entity_id']},
            limit=1
        )
        
        if existing:
            return self.connector.update_node(
                node_properties['entity_id'],
                {k: v for k, v in node_properties.items() if k != 'entity_id'}
            )
        else:
            return self.connector.create_node(
                labels=['Entity', 'Portfolio'],
                properties=node_properties
            )
    
    def build_asset_node(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update asset node"""
        node_properties = {
            'entity_id': asset_data['asset_id'],
            'entity_type': 'asset',
            'name': asset_data.get('asset_name', asset_data['asset_id']),
            'asset_type': asset_data.get('asset_type', 'equity'),
            'ticker': asset_data.get('ticker', asset_data['asset_id']),
            'sector': asset_data.get('sector'),
            'current_price': asset_data.get('current_price'),
            'volatility': asset_data.get('volatility', 0.25),
            'risk_score': asset_data.get('risk_score', 0.5),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        existing = self.connector.find_nodes(
            labels=['Asset'],
            properties={'entity_id': node_properties['entity_id']},
            limit=1
        )
        
        if existing:
            return self.connector.update_node(
                node_properties['entity_id'],
                {k: v for k, v in node_properties.items() if k != 'entity_id'}
            )
        else:
            return self.connector.create_node(
                labels=['Entity', 'Asset'],
                properties=node_properties
            )
    
    def build_counterparty_node(self, cp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update counterparty node"""
        node_properties = {
            'entity_id': cp_data['counterparty_id'],
            'entity_type': 'counterparty',
            'name': cp_data['counterparty_name'],
            'counterparty_type': cp_data.get('counterparty_type', 'unknown'),
            'credit_rating': cp_data.get('credit_rating'),
            'country': cp_data.get('country'),
            'industry': cp_data.get('industry'),
            'total_exposure': cp_data.get('total_exposure', 0),
            'risk_score': cp_data.get('risk_score', 0.5),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        existing = self.connector.find_nodes(
            labels=['Counterparty'],
            properties={'entity_id': node_properties['entity_id']},
            limit=1
        )
        
        if existing:
            return self.connector.update_node(
                node_properties['entity_id'],
                {k: v for k, v in node_properties.items() if k != 'entity_id'}
            )
        else:
            return self.connector.create_node(
                labels=['Entity', 'Counterparty'],
                properties=node_properties
            )
    
    def create_contains_relationship(
        self,
        portfolio_id: str,
        asset_id: str,
        position_data: Dict[str, Any]
    ) -> None:
        """Create CONTAINS relationship between portfolio and asset"""
        query = """
            MATCH (p:Portfolio {entity_id: $portfolio_id})
            MATCH (a:Asset {entity_id: $asset_id})
            MERGE (p)-[r:CONTAINS]->(a)
            SET r.quantity = $quantity,
                r.weight = $weight,
                r.cost_basis = $cost_basis,
                r.market_value = $market_value,
                r.unrealized_pnl = $unrealized_pnl,
                r.timestamp = datetime()
            RETURN r
        """
        
        params = {
            'portfolio_id': portfolio_id,
            'asset_id': asset_id,
            'quantity': position_data.get('quantity', 0),
            'weight': position_data.get('weight', 0),
            'cost_basis': position_data.get('average_cost'),
            'market_value': position_data.get('market_value'),
            'unrealized_pnl': position_data.get('unrealized_pnl')
        }
        
        self.connector.execute_write(query, params)
    
    def create_transacts_with_relationship(
        self,
        portfolio_id: str,
        counterparty_id: str,
        transaction_stats: Dict[str, Any]
    ) -> None:
        """Create or update TRANSACTS_WITH relationship"""
        query = """
            MATCH (p:Portfolio {entity_id: $portfolio_id})
            MATCH (c:Counterparty {entity_id: $counterparty_id})
            MERGE (p)-[r:TRANSACTS_WITH]->(c)
            SET r.transaction_count = $transaction_count,
                r.total_volume = $total_volume,
                r.avg_transaction_size = $avg_transaction_size,
                r.weight = $weight,
                r.last_transaction = $last_transaction,
                r.risk_contribution = $risk_contribution
            RETURN r
        """
        
        params = {
            'portfolio_id': portfolio_id,
            'counterparty_id': counterparty_id,
            'transaction_count': transaction_stats.get('transaction_count', 0),
            'total_volume': transaction_stats.get('total_volume', 0),
            'avg_transaction_size': transaction_stats.get('avg_transaction_size', 0),
            'weight': transaction_stats.get('weight', 0.5),
            'last_transaction': transaction_stats.get('last_transaction', datetime.now().isoformat()),
            'risk_contribution': transaction_stats.get('risk_contribution', 0.5)
        }
        
        self.connector.execute_write(query, params)
    
    def create_correlates_with_relationship(
        self,
        asset1_id: str,
        asset2_id: str,
        correlation_data: Dict[str, Any]
    ) -> None:
        """Create CORRELATES_WITH relationship between assets"""
        query = """
            MATCH (a1:Asset {entity_id: $asset1_id})
            MATCH (a2:Asset {entity_id: $asset2_id})
            MERGE (a1)-[r:CORRELATES_WITH]->(a2)
            SET r.correlation_coefficient = $correlation_coefficient,
                r.correlation_type = $correlation_type,
                r.lookback_period = $lookback_period,
                r.timestamp = datetime(),
                r.significance = $significance
            RETURN r
        """
        
        params = {
            'asset1_id': asset1_id,
            'asset2_id': asset2_id,
            'correlation_coefficient': correlation_data.get('correlation_coefficient', 0),
            'correlation_type': correlation_data.get('correlation_type', 'price'),
            'lookback_period': correlation_data.get('lookback_period', 252),
            'significance': correlation_data.get('significance', 0.05)
        }
        
        self.connector.execute_write(query, params)
    
    def build_graph_from_portfolios(self, portfolios: List[Dict[str, Any]]) -> Dict[str, int]:
        """Build graph from portfolio data"""
        stats = {'portfolios': 0, 'assets': 0, 'relationships': 0}
        
        for portfolio in portfolios:
            try:
                self.build_portfolio_node(portfolio)
                stats['portfolios'] += 1
                
                # Build asset nodes and relationships from positions
                if 'positions' in portfolio:
                    for position in portfolio['positions']:
                        self.build_asset_node({'asset_id': position['asset_id']})
                        stats['assets'] += 1
                        
                        self.create_contains_relationship(
                            portfolio['portfolio_id'],
                            position['asset_id'],
                            position
                        )
                        stats['relationships'] += 1
                        
            except Exception as e:
                logger.error(f"Failed to build graph for portfolio {portfolio.get('portfolio_id')}: {e}")
        
        return stats
    
    def update_graph_incrementally(
        self,
        entity_type: str,
        entity_data: Dict[str, Any]
    ) -> bool:
        """Update graph incrementally with new data"""
        try:
            if entity_type == 'portfolio':
                self.build_portfolio_node(entity_data)
            elif entity_type == 'asset':
                self.build_asset_node(entity_data)
            elif entity_type == 'counterparty':
                self.build_counterparty_node(entity_data)
            else:
                logger.warning(f"Unknown entity type: {entity_type}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to update graph for {entity_type}: {e}")
            return False
    
    def ensure_graph_consistency(self) -> Dict[str, Any]:
        """Check and ensure graph consistency"""
        query = """
            MATCH (n:Entity)
            WHERE NOT EXISTS(n.updated_at)
            SET n.updated_at = datetime()
            RETURN count(n) as updated_count
        """
        
        result = self.connector.execute_write(query)
        return {'updated_nodes': result[0]['updated_count'] if result else 0}


# Example usage
if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    connector = Neo4jConnector(
        uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        password=os.getenv('NEO4J_PASSWORD', 'password')
    )
    
    service = GraphBuilderService(connector)
    
    # Example: Build portfolio node
    portfolio = {
        'portfolio_id': 'portfolio_test',
        'portfolio_name': 'Test Portfolio',
        'portfolio_type': 'equity',
        'total_value': 1000000.00
    }
    
    try:
        result = service.build_portfolio_node(portfolio)
        print(f"✓ Created/updated portfolio node: {result}")
    finally:
        connector.close()

# Made with Bob
