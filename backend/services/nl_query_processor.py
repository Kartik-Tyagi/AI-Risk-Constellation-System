"""
Natural Language Query Processor
Parses natural language queries and executes them against the risk system
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NLQueryProcessor:
    """Process natural language queries about risk"""

    def __init__(self, db_manager, neo4j_manager, inference_engine):
        """
        Initialize the NL query processor
        
        Args:
            db_manager: PostgreSQL database manager
            neo4j_manager: Neo4j graph database manager
            inference_engine: ML inference engine
        """
        self.db = db_manager
        self.neo4j = neo4j_manager
        self.inference = inference_engine
        
        # Query patterns
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize regex patterns for query matching"""
        return {
            'risk_assessment': [
                {
                    'pattern': r'(?:what is|show|get|calculate).*risk.*(?:of|for)\s+(?:portfolio|entity)?\s*([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_assessment
                },
                {
                    'pattern': r'(?:show|list|get).*(?:highest|high|top).*risk.*entities?',
                    'handler': self._handle_high_risk_entities
                },
                {
                    'pattern': r'(?:what are|show|list).*risk factors.*(?:for|of)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_factors
                },
                {
                    'pattern': r'calculate.*overall.*portfolio.*risk',
                    'handler': self._handle_overall_risk
                },
            ],
            'correlation': [
                {
                    'pattern': r'(?:show|find|get).*entities.*(?:high|strong).*correlation.*(?:to|with)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_correlation_query
                },
                {
                    'pattern': r'(?:what|which).*entities.*most.*correlated',
                    'handler': self._handle_most_correlated
                },
                {
                    'pattern': r'(?:find|show).*entities.*negative.*correlation.*(?:to|with)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_negative_correlation
                },
                {
                    'pattern': r'(?:show|display).*correlation.*matrix',
                    'handler': self._handle_correlation_matrix
                },
            ],
            'propagation': [
                {
                    'pattern': r'(?:predict|show|calculate).*risk.*cascade.*(?:from|of)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_cascade
                },
                {
                    'pattern': r'what.*happens.*if\s+([A-Za-z0-9_-]+).*fails?',
                    'handler': self._handle_failure_scenario
                },
                {
                    'pattern': r'(?:show|display).*risk.*propagation.*paths?.*(?:from|of)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_propagation_paths
                },
                {
                    'pattern': r'(?:which|what).*entities.*(?:affected|impacted).*by\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_affected_entities
                },
            ],
            'comparison': [
                {
                    'pattern': r'compare.*risk.*(?:profiles?|of)\s+([A-Za-z0-9_-]+).*(?:and|vs|versus)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_comparison
                },
                {
                    'pattern': r'(?:which|who).*(?:has|have).*(?:higher|lower).*risk.*([A-Za-z0-9_-]+).*(?:or|vs)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_comparison
                },
                {
                    'pattern': r'(?:show|display).*differences?.*between\s+([A-Za-z0-9_-]+).*(?:and|vs)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_differences
                },
                {
                    'pattern': r'compare.*risk.*dna.*(?:of|for)\s+([A-Za-z0-9_-]+).*(?:and|vs)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_dna_comparison
                },
            ],
            'temporal': [
                {
                    'pattern': r'how.*risk.*changed.*(?:for|of)\s+([A-Za-z0-9_-]+).*over.*time',
                    'handler': self._handle_risk_over_time
                },
                {
                    'pattern': r'(?:show|display).*risk.*trends?.*(?:for|of).*(?:past|last)\s+(\d+)\s*(day|week|month|year)s?',
                    'handler': self._handle_risk_trends
                },
                {
                    'pattern': r'when.*(?:did|was)\s+([A-Za-z0-9_-]+).*(?:highest|peak).*risk',
                    'handler': self._handle_peak_risk
                },
                {
                    'pattern': r'predict.*future.*risk.*(?:for|of)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_risk_prediction
                },
            ],
            'optimization': [
                {
                    'pattern': r'optimize.*portfolio.*(?:to\s+)?minimize.*risk',
                    'handler': self._handle_portfolio_optimization
                },
                {
                    'pattern': r'suggest.*portfolio.*rebalanc(?:e|ing)',
                    'handler': self._handle_rebalancing
                },
                {
                    'pattern': r'(?:what is|find).*optimal.*allocation.*(?:for|of)\s+([A-Za-z0-9_-]+)',
                    'handler': self._handle_optimal_allocation
                },
                {
                    'pattern': r'find.*best.*risk.*return.*trade.*off',
                    'handler': self._handle_risk_return_tradeoff
                },
            ],
        }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query
        
        Args:
            query: Natural language query string
            
        Returns:
            Dict containing query results
        """
        start_time = datetime.now()
        query_lower = query.lower().strip()
        
        logger.info(f"Processing NL query: {query}")
        
        # Try to match query to patterns
        for query_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                match = re.search(pattern_info['pattern'], query_lower, re.IGNORECASE)
                if match:
                    try:
                        # Extract parameters from match
                        params = list(match.groups())
                        
                        # Call handler
                        results = await pattern_info['handler'](*params)
                        
                        execution_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        return {
                            'query_type': query_type,
                            'results': results,
                            'visualization_type': self._get_visualization_type(query_type),
                            'metadata': {
                                'execution_time': execution_time,
                                'confidence': 0.9,  # Could be calculated based on pattern match quality
                                'query_pattern': pattern_info['pattern'],
                            }
                        }
                    except Exception as e:
                        logger.error(f"Error processing query: {e}")
                        raise
        
        # No pattern matched
        return {
            'query_type': 'unknown',
            'results': None,
            'error': 'Could not understand the query. Please try rephrasing.',
            'metadata': {
                'execution_time': (datetime.now() - start_time).total_seconds() * 1000,
                'confidence': 0.0,
            }
        }
    
    def _get_visualization_type(self, query_type: str) -> str:
        """Get recommended visualization type for query type"""
        viz_map = {
            'risk_assessment': 'table',
            'correlation': 'heatmap',
            'propagation': 'graph',
            'comparison': 'bar_chart',
            'temporal': 'line_chart',
            'optimization': 'table',
        }
        return viz_map.get(query_type, 'table')
    
    # Risk Assessment Handlers
    
    async def _handle_risk_assessment(self, entity_id: str) -> Dict[str, Any]:
        """Handle risk assessment query for specific entity"""
        # Get risk calculation from inference engine
        risk_data = await self.inference.calculate_risk(entity_id)
        
        return {
            'entity_id': entity_id,
            'risk_level': risk_data['risk_level'],
            'risk_score': risk_data['risk_score'],
            'risk_factors': risk_data['factors'],
            'confidence': risk_data['confidence'],
        }
    
    async def _handle_high_risk_entities(self) -> List[Dict[str, Any]]:
        """Handle query for highest risk entities"""
        # Query database for high risk entities
        query = """
            SELECT entity_id, risk_score, risk_level
            FROM risk_calculations
            WHERE calculation_date = (SELECT MAX(calculation_date) FROM risk_calculations)
            ORDER BY risk_score DESC
            LIMIT 10
        """
        results = await self.db.fetch_all(query)
        
        return [
            {
                'entity_id': row['entity_id'],
                'risk_score': float(row['risk_score']),
                'risk_level': row['risk_level'],
            }
            for row in results
        ]
    
    async def _handle_risk_factors(self, entity_id: str) -> Dict[str, Any]:
        """Handle query for risk factors of entity"""
        risk_data = await self.inference.calculate_risk(entity_id)
        
        return {
            'entity_id': entity_id,
            'risk_factors': risk_data['factors'],
            'factor_contributions': risk_data.get('factor_contributions', {}),
        }
    
    async def _handle_overall_risk(self) -> Dict[str, Any]:
        """Handle query for overall portfolio risk"""
        # Calculate aggregate risk across all entities
        query = """
            SELECT 
                AVG(risk_score) as avg_risk,
                MAX(risk_score) as max_risk,
                MIN(risk_score) as min_risk,
                STDDEV(risk_score) as risk_volatility
            FROM risk_calculations
            WHERE calculation_date = (SELECT MAX(calculation_date) FROM risk_calculations)
        """
        result = await self.db.fetch_one(query)
        
        return {
            'average_risk': float(result['avg_risk']),
            'maximum_risk': float(result['max_risk']),
            'minimum_risk': float(result['min_risk']),
            'risk_volatility': float(result['risk_volatility']),
        }
    
    # Correlation Handlers
    
    async def _handle_correlation_query(self, entity_id: str) -> List[Dict[str, Any]]:
        """Handle correlation query"""
        # Query Neo4j for correlated entities
        cypher = """
            MATCH (e1:Entity {id: $entity_id})-[r:CORRELATED_WITH]-(e2:Entity)
            WHERE r.correlation > 0.6
            RETURN e2.id as entity_id, r.correlation as correlation
            ORDER BY r.correlation DESC
            LIMIT 10
        """
        results = await self.neo4j.run_query(cypher, {'entity_id': entity_id})
        
        return [
            {
                'entity1': entity_id,
                'entity2': row['entity_id'],
                'correlation': float(row['correlation']),
            }
            for row in results
        ]
    
    async def _handle_most_correlated(self) -> List[Dict[str, Any]]:
        """Handle query for most correlated entities"""
        cypher = """
            MATCH (e1:Entity)-[r:CORRELATED_WITH]-(e2:Entity)
            WHERE e1.id < e2.id
            RETURN e1.id as entity1, e2.id as entity2, r.correlation as correlation
            ORDER BY ABS(r.correlation) DESC
            LIMIT 10
        """
        results = await self.neo4j.run_query(cypher)
        
        return [
            {
                'entity1': row['entity1'],
                'entity2': row['entity2'],
                'correlation': float(row['correlation']),
            }
            for row in results
        ]
    
    async def _handle_negative_correlation(self, entity_id: str) -> List[Dict[str, Any]]:
        """Handle negative correlation query"""
        cypher = """
            MATCH (e1:Entity {id: $entity_id})-[r:CORRELATED_WITH]-(e2:Entity)
            WHERE r.correlation < -0.3
            RETURN e2.id as entity_id, r.correlation as correlation
            ORDER BY r.correlation ASC
            LIMIT 10
        """
        results = await self.neo4j.run_query(cypher, {'entity_id': entity_id})
        
        return [
            {
                'entity1': entity_id,
                'entity2': row['entity_id'],
                'correlation': float(row['correlation']),
            }
            for row in results
        ]
    
    async def _handle_correlation_matrix(self) -> Dict[str, Any]:
        """Handle correlation matrix query"""
        # Get top entities and their correlations
        cypher = """
            MATCH (e1:Entity)-[r:CORRELATED_WITH]-(e2:Entity)
            WHERE e1.id < e2.id
            RETURN e1.id as entity1, e2.id as entity2, r.correlation as correlation
            LIMIT 100
        """
        results = await self.neo4j.run_query(cypher)
        
        # Build correlation matrix
        entities = set()
        correlations = {}
        
        for row in results:
            e1, e2 = row['entity1'], row['entity2']
            entities.add(e1)
            entities.add(e2)
            correlations[(e1, e2)] = float(row['correlation'])
            correlations[(e2, e1)] = float(row['correlation'])
        
        return {
            'entities': sorted(list(entities)),
            'correlations': correlations,
        }
    
    # Propagation Handlers
    
    async def _handle_risk_cascade(self, entity_id: str) -> Dict[str, Any]:
        """Handle risk cascade prediction"""
        # Use graph traversal to find cascade
        cypher = """
            MATCH path = (source:Entity {id: $entity_id})-[:INFLUENCES*1..3]->(target:Entity)
            WITH target, length(path) as depth, 
                 reduce(impact = 1.0, r in relationships(path) | impact * r.weight) as total_impact
            RETURN target.id as entity_id, depth, total_impact
            ORDER BY total_impact DESC
            LIMIT 20
        """
        results = await self.neo4j.run_query(cypher, {'entity_id': entity_id})
        
        affected_entities = [
            {
                'id': row['entity_id'],
                'depth': row['depth'],
                'impact': float(row['total_impact']),
            }
            for row in results
        ]
        
        return {
            'source_entity': entity_id,
            'affected_entities': affected_entities,
            'total_impact': sum(e['impact'] for e in affected_entities),
            'cascade_depth': max((e['depth'] for e in affected_entities), default=0),
        }
    
    async def _handle_failure_scenario(self, entity_id: str) -> Dict[str, Any]:
        """Handle failure scenario query"""
        return await self._handle_risk_cascade(entity_id)
    
    async def _handle_propagation_paths(self, entity_id: str) -> Dict[str, Any]:
        """Handle propagation paths query"""
        cypher = """
            MATCH path = (source:Entity {id: $entity_id})-[:INFLUENCES*1..3]->(target:Entity)
            RETURN [node in nodes(path) | node.id] as path,
                   reduce(weight = 1.0, r in relationships(path) | weight * r.weight) as path_weight
            ORDER BY path_weight DESC
            LIMIT 10
        """
        results = await self.neo4j.run_query(cypher, {'entity_id': entity_id})
        
        return {
            'source_entity': entity_id,
            'paths': [
                {
                    'nodes': row['path'],
                    'weight': float(row['path_weight']),
                }
                for row in results
            ],
        }
    
    async def _handle_affected_entities(self, entity_id: str) -> Dict[str, Any]:
        """Handle affected entities query"""
        return await self._handle_risk_cascade(entity_id)
    
    # Comparison Handlers
    
    async def _handle_risk_comparison(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """Handle risk comparison query"""
        risk1 = await self.inference.calculate_risk(entity1)
        risk2 = await self.inference.calculate_risk(entity2)
        
        winner = entity1 if risk1['risk_score'] < risk2['risk_score'] else entity2
        
        return {
            'entities': [entity1, entity2],
            'metrics': {
                'risk_score': [risk1['risk_score'], risk2['risk_score']],
                'risk_level': [risk1['risk_level'], risk2['risk_level']],
            },
            'winner': winner,
            'summary': f"{winner} has lower risk than the other entity",
        }
    
    async def _handle_differences(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """Handle differences query"""
        return await self._handle_risk_comparison(entity1, entity2)
    
    async def _handle_dna_comparison(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """Handle DNA comparison query"""
        dna1 = await self.inference.get_risk_dna(entity1)
        dna2 = await self.inference.get_risk_dna(entity2)
        
        # Calculate similarity
        similarity = self._calculate_dna_similarity(dna1, dna2)
        
        return {
            'entities': [entity1, entity2],
            'dna1': dna1,
            'dna2': dna2,
            'similarity': similarity,
            'summary': f"Risk DNA similarity: {similarity:.2%}",
        }
    
    def _calculate_dna_similarity(self, dna1: List[float], dna2: List[float]) -> float:
        """Calculate cosine similarity between two DNA vectors"""
        import numpy as np
        
        dna1_arr = np.array(dna1)
        dna2_arr = np.array(dna2)
        
        dot_product = np.dot(dna1_arr, dna2_arr)
        norm1 = np.linalg.norm(dna1_arr)
        norm2 = np.linalg.norm(dna2_arr)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    # Temporal Handlers
    
    async def _handle_risk_over_time(self, entity_id: str) -> Dict[str, Any]:
        """Handle risk over time query"""
        query = """
            SELECT calculation_date, risk_score, risk_level
            FROM risk_calculations
            WHERE entity_id = $1
            ORDER BY calculation_date DESC
            LIMIT 100
        """
        results = await self.db.fetch_all(query, entity_id)
        
        time_series = [
            {
                'timestamp': row['calculation_date'].isoformat(),
                'value': float(row['risk_score']),
                'level': row['risk_level'],
            }
            for row in results
        ]
        
        # Calculate trend
        if len(time_series) >= 2:
            recent_avg = sum(t['value'] for t in time_series[:10]) / 10
            older_avg = sum(t['value'] for t in time_series[-10:]) / 10
            trend = 'increasing' if recent_avg > older_avg else 'decreasing' if recent_avg < older_avg else 'stable'
        else:
            trend = 'stable'
        
        return {
            'entity': entity_id,
            'time_series': time_series,
            'trend': trend,
            'anomalies': [],  # Could detect anomalies
            'statistics': {
                'mean': sum(t['value'] for t in time_series) / len(time_series) if time_series else 0,
                'max': max((t['value'] for t in time_series), default=0),
                'min': min((t['value'] for t in time_series), default=0),
            },
        }
    
    async def _handle_risk_trends(self, period: str, unit: str) -> Dict[str, Any]:
        """Handle risk trends query"""
        # Calculate date range
        period_int = int(period)
        if unit.startswith('day'):
            delta = timedelta(days=period_int)
        elif unit.startswith('week'):
            delta = timedelta(weeks=period_int)
        elif unit.startswith('month'):
            delta = timedelta(days=period_int * 30)
        else:  # year
            delta = timedelta(days=period_int * 365)
        
        start_date = datetime.now() - delta
        
        query = """
            SELECT calculation_date, AVG(risk_score) as avg_risk
            FROM risk_calculations
            WHERE calculation_date >= $1
            GROUP BY calculation_date
            ORDER BY calculation_date
        """
        results = await self.db.fetch_all(query, start_date)
        
        return {
            'period': f"{period} {unit}",
            'time_series': [
                {
                    'timestamp': row['calculation_date'].isoformat(),
                    'value': float(row['avg_risk']),
                }
                for row in results
            ],
        }
    
    async def _handle_peak_risk(self, entity_id: str) -> Dict[str, Any]:
        """Handle peak risk query"""
        query = """
            SELECT calculation_date, risk_score
            FROM risk_calculations
            WHERE entity_id = $1
            ORDER BY risk_score DESC
            LIMIT 1
        """
        result = await self.db.fetch_one(query, entity_id)
        
        if result:
            return {
                'entity': entity_id,
                'peak_date': result['calculation_date'].isoformat(),
                'peak_risk': float(result['risk_score']),
            }
        return {'entity': entity_id, 'peak_date': None, 'peak_risk': 0}
    
    async def _handle_risk_prediction(self, entity_id: str) -> Dict[str, Any]:
        """Handle risk prediction query"""
        # Use temporal model for prediction
        predictions = await self.inference.predict_future_risk(entity_id, days=30)
        
        return {
            'entity': entity_id,
            'predictions': predictions,
            'confidence': 0.75,  # Model confidence
        }
    
    # Optimization Handlers
    
    async def _handle_portfolio_optimization(self) -> Dict[str, Any]:
        """Handle portfolio optimization query"""
        # Use quantum optimizer
        optimization_result = await self.inference.optimize_portfolio()
        
        return {
            'current_allocation': optimization_result['current'],
            'optimized_allocation': optimization_result['optimized'],
            'expected_improvement': optimization_result['improvement'],
            'risk_reduction': optimization_result['risk_reduction'],
            'recommendations': optimization_result['recommendations'],
        }
    
    async def _handle_rebalancing(self) -> Dict[str, Any]:
        """Handle rebalancing query"""
        return await self._handle_portfolio_optimization()
    
    async def _handle_optimal_allocation(self, portfolio_id: str) -> Dict[str, Any]:
        """Handle optimal allocation query"""
        optimization_result = await self.inference.optimize_portfolio(portfolio_id)
        
        return {
            'portfolio': portfolio_id,
            'optimized_allocation': optimization_result['optimized'],
            'expected_improvement': optimization_result['improvement'],
            'recommendations': optimization_result['recommendations'],
        }
    
    async def _handle_risk_return_tradeoff(self) -> Dict[str, Any]:
        """Handle risk-return tradeoff query"""
        # Calculate efficient frontier
        frontier = await self.inference.calculate_efficient_frontier()
        
        return {
            'efficient_frontier': frontier,
            'optimal_point': frontier['optimal'],
            'recommendations': frontier['recommendations'],
        }


# Made with Bob