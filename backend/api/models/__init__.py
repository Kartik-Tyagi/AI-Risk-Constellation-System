"""
API Models Package
Pydantic models for request/response validation
"""

from backend.api.models.portfolio import (
    PortfolioPosition,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioRiskMetrics,
    PortfolioRiskResponse,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse
)

from backend.api.models.risk import (
    RiskCalculationRequest,
    RiskMetrics,
    RiskDNA,
    RiskPropagationPath,
    RiskCalculationResponse,
    RiskHistoryRequest,
    RiskHistoryPoint,
    RiskHistoryResponse,
    RiskComparisonRequest,
    RiskComparisonEntity,
    RiskComparisonResponse,
    RiskDNAResponse
)

from backend.api.models.entity import (
    EntityBase,
    EntityCreate,
    EntityUpdate,
    EntityRelationship,
    EntityResponse,
    EntityListResponse,
    EntitySearchRequest,
    EntityNetworkRequest,
    EntityNetworkNode,
    EntityNetworkEdge,
    EntityNetworkResponse
)

from backend.api.models.query import (
    GraphQueryRequest,
    ConstellationNode,
    ConstellationEdge,
    ConstellationResponse,
    PropagationPath,
    PropagationResponse,
    CascadeScenario,
    CascadePredictionRequest,
    CascadePredictionResponse,
    MarketDataRequest,
    MarketDataPoint,
    MarketDataResponse,
    MarketConditionsResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    PaginationParams,
    SortParams,
    FilterParams
)

__all__ = [
    # Portfolio models
    "PortfolioPosition",
    "PortfolioCreate",
    "PortfolioUpdate",
    "PortfolioResponse",
    "PortfolioListResponse",
    "PortfolioRiskMetrics",
    "PortfolioRiskResponse",
    "PortfolioOptimizationRequest",
    "PortfolioOptimizationResponse",
    
    # Risk models
    "RiskCalculationRequest",
    "RiskMetrics",
    "RiskDNA",
    "RiskPropagationPath",
    "RiskCalculationResponse",
    "RiskHistoryRequest",
    "RiskHistoryPoint",
    "RiskHistoryResponse",
    "RiskComparisonRequest",
    "RiskComparisonEntity",
    "RiskComparisonResponse",
    "RiskDNAResponse",
    
    # Entity models
    "EntityBase",
    "EntityCreate",
    "EntityUpdate",
    "EntityRelationship",
    "EntityResponse",
    "EntityListResponse",
    "EntitySearchRequest",
    "EntityNetworkRequest",
    "EntityNetworkNode",
    "EntityNetworkEdge",
    "EntityNetworkResponse",
    
    # Query models
    "GraphQueryRequest",
    "ConstellationNode",
    "ConstellationEdge",
    "ConstellationResponse",
    "PropagationPath",
    "PropagationResponse",
    "CascadeScenario",
    "CascadePredictionRequest",
    "CascadePredictionResponse",
    "MarketDataRequest",
    "MarketDataPoint",
    "MarketDataResponse",
    "MarketConditionsResponse",
    "NaturalLanguageQueryRequest",
    "NaturalLanguageQueryResponse",
    "PaginationParams",
    "SortParams",
    "FilterParams"
]

# Made with Bob
