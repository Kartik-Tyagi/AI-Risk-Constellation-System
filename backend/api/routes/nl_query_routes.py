"""
Natural Language Query Routes
API endpoints for natural language queries
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import (
    get_postgres_dependency,
    get_neo4j_dependency,
    get_ml_models_dependency
)
from backend.services.nl_query_processor import NLQueryProcessor

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class NLQueryRequest(BaseModel):
    """Natural language query request"""
    query: str


class NLQueryResponse(BaseModel):
    """Natural language query response"""
    query_type: str
    results: dict
    visualization_type: str
    metadata: dict
    error: Optional[str] = None


class QuerySuggestionsRequest(BaseModel):
    """Query suggestions request"""
    q: str


class QuerySuggestionsResponse(BaseModel):
    """Query suggestions response"""
    suggestions: List[str]


# Dependency to get NL query processor
async def get_nl_processor(
    db=Depends(get_postgres_dependency),
    graph_db=Depends(get_neo4j_dependency),
    ml_models=Depends(get_ml_models_dependency)
) -> NLQueryProcessor:
    """Get NL query processor instance"""
    return NLQueryProcessor(db, graph_db, ml_models)


@router.post("/nl-query", response_model=NLQueryResponse)
async def process_nl_query(
    request: NLQueryRequest,
    processor: NLQueryProcessor = Depends(get_nl_processor)
):
    """
    Process a natural language query
    
    Args:
        request: NL query request
        processor: NL query processor
        
    Returns:
        Query results
    """
    try:
        logger.info(f"Processing NL query: {request.query}")
        
        # Process the query
        result = await processor.process_query(request.query)
        
        return NLQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing NL query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/nl-query/suggestions", response_model=QuerySuggestionsResponse)
async def get_query_suggestions(
    q: str,
    processor: NLQueryProcessor = Depends(get_nl_processor)
):
    """
    Get query suggestions based on partial input
    
    Args:
        q: Partial query text
        processor: NL query processor
        
    Returns:
        List of suggested queries
    """
    try:
        # Generate suggestions based on query patterns
        suggestions = []
        
        q_lower = q.lower()
        
        # Risk assessment suggestions
        if any(word in q_lower for word in ['risk', 'what', 'show']):
            suggestions.extend([
                'What is the risk of portfolio ABC?',
                'Show me the highest risk entities',
                'What are the risk factors for entity XYZ?',
            ])
        
        # Correlation suggestions
        if any(word in q_lower for word in ['correlation', 'correlated', 'related']):
            suggestions.extend([
                'Show me entities with high correlation to ABC',
                'What entities are most correlated?',
                'Find entities with negative correlation to XYZ',
            ])
        
        # Propagation suggestions
        if any(word in q_lower for word in ['cascade', 'propagation', 'impact', 'affect']):
            suggestions.extend([
                'Predict risk cascade from entity ABC',
                'What happens if entity XYZ fails?',
                'Which entities would be affected by ABC?',
            ])
        
        # Comparison suggestions
        if any(word in q_lower for word in ['compare', 'comparison', 'versus', 'vs']):
            suggestions.extend([
                'Compare risk profiles of ABC and XYZ',
                'Which has higher risk: ABC or XYZ?',
                'Compare risk DNA of ABC and XYZ',
            ])
        
        # Temporal suggestions
        if any(word in q_lower for word in ['time', 'trend', 'history', 'changed']):
            suggestions.extend([
                'How has risk changed for ABC over time?',
                'Show risk trends for the past 30 days',
                'Predict future risk for entity XYZ',
            ])
        
        # Optimization suggestions
        if any(word in q_lower for word in ['optimize', 'optimal', 'best', 'rebalance']):
            suggestions.extend([
                'Optimize portfolio to minimize risk',
                'Suggest portfolio rebalancing',
                'Find the best risk-return trade-off',
            ])
        
        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions = [
                'What is the risk of portfolio ABC?',
                'Show me entities with high correlation to XYZ',
                'Predict risk cascade from entity ABC',
                'Compare risk profiles of ABC and XYZ',
                'How has risk changed for ABC over time?',
                'Optimize portfolio to minimize risk',
            ]
        
        # Limit to 10 suggestions
        return QuerySuggestionsResponse(suggestions=suggestions[:10])
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return QuerySuggestionsResponse(suggestions=[])


@router.get("/nl-query/templates")
async def get_query_templates():
    """
    Get all available query templates
    
    Returns:
        Dictionary of query templates by category
    """
    templates = {
        'risk_assessment': [
            'What is the risk of portfolio {name}?',
            'Show me the highest risk entities',
            'What are the risk factors for {entity}?',
            'Calculate the overall portfolio risk',
        ],
        'correlation': [
            'Show me entities with high correlation to {entity}',
            'What entities are most correlated?',
            'Find entities with negative correlation to {entity}',
            'Show correlation matrix for top 10 entities',
        ],
        'propagation': [
            'Predict risk cascade from {entity}',
            'What happens if {entity} fails?',
            'Show risk propagation paths from {entity}',
            'Which entities would be affected by {entity}?',
        ],
        'comparison': [
            'Compare risk profiles of {entity1} and {entity2}',
            'Which has higher risk: {entity1} or {entity2}?',
            'Show differences between {portfolio1} and {portfolio2}',
            'Compare risk DNA of {entity1} and {entity2}',
        ],
        'temporal': [
            'How has risk changed for {entity} over time?',
            'Show risk trends for the past {period}',
            'When did {entity} have the highest risk?',
            'Predict future risk for {entity}',
        ],
        'optimization': [
            'Optimize portfolio to minimize risk',
            'Suggest portfolio rebalancing',
            'What is the optimal allocation for {portfolio}?',
            'Find the best risk-return trade-off',
        ],
    }
    
    return templates


@router.get("/nl-query/examples")
async def get_query_examples():
    """
    Get example queries with expected results
    
    Returns:
        List of example queries
    """
    examples = [
        {
            'query': 'What is the risk of portfolio TECH-001?',
            'type': 'risk_assessment',
            'description': 'Get risk assessment for a specific portfolio',
        },
        {
            'query': 'Show me entities with high correlation to AAPL',
            'type': 'correlation',
            'description': 'Find entities highly correlated with AAPL',
        },
        {
            'query': 'Predict risk cascade from BANK-001',
            'type': 'propagation',
            'description': 'Predict how risk would propagate from BANK-001',
        },
        {
            'query': 'Compare risk profiles of TECH-001 and FINANCE-001',
            'type': 'comparison',
            'description': 'Compare risk between two portfolios',
        },
        {
            'query': 'How has risk changed for AAPL over time?',
            'type': 'temporal',
            'description': 'View historical risk trends for AAPL',
        },
        {
            'query': 'Optimize portfolio to minimize risk',
            'type': 'optimization',
            'description': 'Get optimal portfolio allocation',
        },
    ]
    
    return examples


# Made with Bob