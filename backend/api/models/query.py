"""
Query Pydantic Models
Request and response models for query endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class GraphQueryRequest(BaseModel):
    """Request model for graph queries"""
    entity_id: str = Field(..., description="Entity ID to query")
    query_type: str = Field(..., description="Query type (constellation/propagation/cascade)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "query_type": "constellation",
                "parameters": {
                    "depth": 2,
                    "min_risk_score": 50
                }
            }
        }


class ConstellationNode(BaseModel):
    """Node in risk constellation"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    risk_score: float = Field(..., description="Risk score")
    risk_level: str = Field(..., description="Risk level")
    position: Dict[str, float] = Field(..., description="Node position (x, y, z)")
    size: float = Field(..., description="Node size (based on importance)")


class ConstellationEdge(BaseModel):
    """Edge in risk constellation"""
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    risk_flow: float = Field(..., description="Risk flow strength")
    relationship_type: str = Field(..., description="Relationship type")


class ConstellationResponse(BaseModel):
    """Response model for risk constellation"""
    central_entity_id: str = Field(..., description="Central entity ID")
    nodes: List[ConstellationNode] = Field(..., description="Constellation nodes")
    edges: List[ConstellationEdge] = Field(..., description="Constellation edges")
    clusters: List[Dict[str, Any]] = Field(..., description="Risk clusters")
    statistics: Dict[str, Any] = Field(..., description="Constellation statistics")
    timestamp: datetime = Field(..., description="Query timestamp")


class PropagationPath(BaseModel):
    """Risk propagation path"""
    path: List[str] = Field(..., description="Entity IDs in path")
    path_names: List[str] = Field(..., description="Entity names in path")
    probability: float = Field(..., description="Propagation probability")
    impact: float = Field(..., description="Potential impact")
    time_to_propagate: float = Field(..., description="Estimated time (days)")
    risk_amplification: float = Field(..., description="Risk amplification factor")


class PropagationResponse(BaseModel):
    """Response model for risk propagation"""
    entity_id: str = Field(..., description="Source entity ID")
    entity_name: str = Field(..., description="Source entity name")
    propagation_paths: List[PropagationPath] = Field(..., description="Propagation paths")
    affected_entities: List[Dict[str, Any]] = Field(..., description="Potentially affected entities")
    total_exposure: float = Field(..., description="Total potential exposure")
    timestamp: datetime = Field(..., description="Analysis timestamp")


class CascadeScenario(BaseModel):
    """Cascade scenario"""
    scenario_id: str = Field(..., description="Scenario ID")
    trigger_entity_id: str = Field(..., description="Trigger entity ID")
    affected_entities: List[str] = Field(..., description="Affected entity IDs")
    cascade_sequence: List[Dict[str, Any]] = Field(..., description="Cascade sequence")
    total_impact: float = Field(..., description="Total impact")
    probability: float = Field(..., description="Scenario probability")


class CascadePredictionRequest(BaseModel):
    """Request model for cascade prediction"""
    trigger_entity_id: Optional[str] = Field(None, description="Trigger entity ID")
    scenario_type: str = Field(default="worst_case", description="Scenario type")
    time_horizon: int = Field(default=30, description="Time horizon (days)")
    confidence_level: float = Field(default=0.95, description="Confidence level")
    
    @validator('confidence_level')
    def validate_confidence(cls, v):
        if not 0 < v < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        return v


class CascadePredictionResponse(BaseModel):
    """Response model for cascade prediction"""
    scenarios: List[CascadeScenario] = Field(..., description="Predicted scenarios")
    most_vulnerable: List[Dict[str, Any]] = Field(..., description="Most vulnerable entities")
    systemic_risk_score: float = Field(..., description="Systemic risk score")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")
    timestamp: datetime = Field(..., description="Prediction timestamp")


class MarketDataRequest(BaseModel):
    """Request model for market data"""
    symbols: Optional[List[str]] = Field(None, description="Specific symbols")
    data_type: str = Field(default="all", description="Data type (prices/volatility/all)")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")


class MarketDataPoint(BaseModel):
    """Single market data point"""
    symbol: str = Field(..., description="Market symbol")
    timestamp: datetime = Field(..., description="Data timestamp")
    price: float = Field(..., description="Price")
    volume: Optional[float] = Field(None, description="Volume")
    volatility: Optional[float] = Field(None, description="Volatility")


class MarketDataResponse(BaseModel):
    """Response model for market data"""
    data: List[MarketDataPoint] = Field(..., description="Market data points")
    statistics: Dict[str, Any] = Field(..., description="Market statistics")
    timestamp: datetime = Field(..., description="Query timestamp")


class MarketConditionsResponse(BaseModel):
    """Response model for market conditions"""
    volatility_index: float = Field(..., description="Market volatility index")
    sentiment: str = Field(..., description="Market sentiment")
    risk_appetite: float = Field(..., description="Risk appetite indicator")
    liquidity_index: float = Field(..., description="Liquidity index")
    stress_indicators: Dict[str, float] = Field(..., description="Stress indicators")
    timestamp: datetime = Field(..., description="Conditions timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "volatility_index": 25.5,
                "sentiment": "neutral",
                "risk_appetite": 0.65,
                "liquidity_index": 0.75,
                "stress_indicators": {
                    "credit_spread": 150,
                    "ted_spread": 50,
                    "vix": 25.5
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language query"""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query context")
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Query must be at least 3 characters")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the risk level of Tech Corp?",
                "context": {
                    "user_id": "user123",
                    "session_id": "session456"
                }
            }
        }


class NaturalLanguageQueryResponse(BaseModel):
    """Response model for natural language query"""
    query: str = Field(..., description="Original query")
    intent: str = Field(..., description="Detected intent")
    entities_mentioned: List[str] = Field(..., description="Entities mentioned in query")
    answer: str = Field(..., description="Natural language answer")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data")
    confidence: float = Field(..., description="Answer confidence (0-1)")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    timestamp: datetime = Field(..., description="Query timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the risk level of Tech Corp?",
                "intent": "get_risk_level",
                "entities_mentioned": ["Tech Corp"],
                "answer": "Tech Corp has a medium risk level with a risk score of 65.5.",
                "data": {
                    "entity_id": "ENT001",
                    "risk_score": 65.5,
                    "risk_level": "medium"
                },
                "confidence": 0.95,
                "suggestions": [
                    "View detailed risk analysis for Tech Corp",
                    "Compare Tech Corp with similar entities"
                ],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


class SortParams(BaseModel):
    """Sort parameters"""
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class FilterParams(BaseModel):
    """Filter parameters"""
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")
    search: Optional[str] = Field(None, description="Search query")

# Made with Bob
