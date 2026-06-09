"""
Risk Pydantic Models
Request and response models for risk analysis endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class RiskCalculationRequest(BaseModel):
    """Request model for risk calculation"""
    entity_id: str = Field(..., description="Entity ID to calculate risk for")
    calculation_type: str = Field(
        default="comprehensive",
        description="Type of calculation (comprehensive/quick/detailed)"
    )
    time_horizon: int = Field(default=30, description="Time horizon in days")
    confidence_level: float = Field(default=0.95, description="Confidence level (0-1)")
    include_propagation: bool = Field(default=True, description="Include risk propagation analysis")
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Current market conditions")
    
    @validator('confidence_level')
    def validate_confidence(cls, v):
        if not 0 < v < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        return v
    
    @validator('time_horizon')
    def validate_horizon(cls, v):
        if v <= 0:
            raise ValueError("Time horizon must be positive")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "calculation_type": "comprehensive",
                "time_horizon": 30,
                "confidence_level": 0.95,
                "include_propagation": True,
                "market_conditions": {
                    "volatility_index": 25.5,
                    "market_sentiment": "neutral"
                }
            }
        }


class RiskMetrics(BaseModel):
    """Detailed risk metrics"""
    var_95: float = Field(..., description="Value at Risk (95%)")
    var_99: float = Field(..., description="Value at Risk (99%)")
    cvar: float = Field(..., description="Conditional VaR")
    expected_shortfall: float = Field(..., description="Expected shortfall")
    volatility: float = Field(..., description="Volatility")
    skewness: float = Field(..., description="Distribution skewness")
    kurtosis: float = Field(..., description="Distribution kurtosis")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "var_95": 15000.0,
                "var_99": 25000.0,
                "cvar": 30000.0,
                "expected_shortfall": 35000.0,
                "volatility": 0.25,
                "skewness": -0.5,
                "kurtosis": 3.2,
                "max_drawdown": 0.15
            }
        }


class RiskDNA(BaseModel):
    """Risk DNA fingerprint"""
    market_risk: float = Field(..., description="Market risk component")
    credit_risk: float = Field(..., description="Credit risk component")
    liquidity_risk: float = Field(..., description="Liquidity risk component")
    operational_risk: float = Field(..., description="Operational risk component")
    concentration_risk: float = Field(..., description="Concentration risk component")
    counterparty_risk: float = Field(..., description="Counterparty risk component")
    systemic_risk: float = Field(..., description="Systemic risk component")
    
    @validator('*')
    def validate_risk_component(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Risk components must be between 0 and 1")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "market_risk": 0.35,
                "credit_risk": 0.25,
                "liquidity_risk": 0.15,
                "operational_risk": 0.10,
                "concentration_risk": 0.08,
                "counterparty_risk": 0.05,
                "systemic_risk": 0.02
            }
        }


class RiskPropagationPath(BaseModel):
    """Risk propagation path"""
    path: List[str] = Field(..., description="Entity IDs in propagation path")
    probability: float = Field(..., description="Propagation probability")
    impact: float = Field(..., description="Potential impact")
    risk_amplification: float = Field(..., description="Risk amplification factor")


class RiskCalculationResponse(BaseModel):
    """Response model for risk calculation"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")
    risk_metrics: RiskMetrics = Field(..., description="Detailed risk metrics")
    risk_dna: RiskDNA = Field(..., description="Risk DNA fingerprint")
    propagation_paths: Optional[List[RiskPropagationPath]] = Field(None, description="Risk propagation paths")
    key_drivers: List[Dict[str, Any]] = Field(..., description="Key risk drivers")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")
    confidence: float = Field(..., description="Calculation confidence (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "entity_name": "Tech Corp",
                "timestamp": "2024-01-01T00:00:00Z",
                "risk_score": 65.5,
                "risk_level": "medium",
                "risk_metrics": {
                    "var_95": 15000.0,
                    "var_99": 25000.0,
                    "cvar": 30000.0,
                    "expected_shortfall": 35000.0,
                    "volatility": 0.25,
                    "skewness": -0.5,
                    "kurtosis": 3.2,
                    "max_drawdown": 0.15
                },
                "risk_dna": {
                    "market_risk": 0.35,
                    "credit_risk": 0.25,
                    "liquidity_risk": 0.15,
                    "operational_risk": 0.10,
                    "concentration_risk": 0.08,
                    "counterparty_risk": 0.05,
                    "systemic_risk": 0.02
                },
                "propagation_paths": [
                    {
                        "path": ["ENT001", "ENT002", "ENT003"],
                        "probability": 0.75,
                        "impact": 0.45,
                        "risk_amplification": 1.8
                    }
                ],
                "key_drivers": [
                    {
                        "factor": "market_volatility",
                        "contribution": 0.35,
                        "trend": "increasing"
                    }
                ],
                "recommendations": [
                    "Monitor market volatility closely",
                    "Consider hedging strategies"
                ],
                "confidence": 0.92
            }
        }


class RiskHistoryRequest(BaseModel):
    """Request model for risk history"""
    entity_id: str = Field(..., description="Entity ID")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    limit: int = Field(default=100, description="Maximum number of records")


class RiskHistoryPoint(BaseModel):
    """Single point in risk history"""
    timestamp: datetime = Field(..., description="Timestamp")
    risk_score: float = Field(..., description="Risk score")
    risk_level: str = Field(..., description="Risk level")
    key_metrics: Dict[str, float] = Field(..., description="Key metrics snapshot")


class RiskHistoryResponse(BaseModel):
    """Response model for risk history"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    history: List[RiskHistoryPoint] = Field(..., description="Risk history")
    statistics: Dict[str, Any] = Field(..., description="Historical statistics")
    trends: Dict[str, str] = Field(..., description="Risk trends")


class RiskComparisonRequest(BaseModel):
    """Request model for risk comparison"""
    entity_ids: List[str] = Field(..., description="Entity IDs to compare")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to compare")
    
    @validator('entity_ids')
    def validate_entities(cls, v):
        if len(v) < 2:
            raise ValueError("Must provide at least 2 entities to compare")
        if len(v) > 10:
            raise ValueError("Cannot compare more than 10 entities at once")
        return v


class RiskComparisonEntity(BaseModel):
    """Entity data in comparison"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    risk_score: float = Field(..., description="Risk score")
    risk_level: str = Field(..., description="Risk level")
    risk_dna: RiskDNA = Field(..., description="Risk DNA")
    key_metrics: Dict[str, float] = Field(..., description="Key metrics")


class RiskComparisonResponse(BaseModel):
    """Response model for risk comparison"""
    entities: List[RiskComparisonEntity] = Field(..., description="Compared entities")
    comparison_matrix: Dict[str, List[float]] = Field(..., description="Comparison matrix")
    rankings: Dict[str, List[str]] = Field(..., description="Rankings by metric")
    insights: List[str] = Field(..., description="Comparison insights")
    timestamp: datetime = Field(..., description="Comparison timestamp")


class RiskDNAResponse(BaseModel):
    """Response model for Risk DNA"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    timestamp: datetime = Field(..., description="Generation timestamp")
    risk_dna: RiskDNA = Field(..., description="Risk DNA fingerprint")
    dna_vector: List[float] = Field(..., description="Full DNA vector")
    similar_entities: List[Dict[str, Any]] = Field(..., description="Entities with similar DNA")
    dna_evolution: Optional[List[Dict[str, Any]]] = Field(None, description="DNA evolution over time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "entity_name": "Tech Corp",
                "timestamp": "2024-01-01T00:00:00Z",
                "risk_dna": {
                    "market_risk": 0.35,
                    "credit_risk": 0.25,
                    "liquidity_risk": 0.15,
                    "operational_risk": 0.10,
                    "concentration_risk": 0.08,
                    "counterparty_risk": 0.05,
                    "systemic_risk": 0.02
                },
                "dna_vector": [0.35, 0.25, 0.15, 0.10, 0.08, 0.05, 0.02],
                "similar_entities": [
                    {
                        "entity_id": "ENT002",
                        "entity_name": "Tech Corp 2",
                        "similarity": 0.85
                    }
                ],
                "dna_evolution": [
                    {
                        "timestamp": "2024-01-01T00:00:00Z",
                        "risk_dna": {
                            "market_risk": 0.30,
                            "credit_risk": 0.28
                        }
                    }
                ]
            }
        }

# Made with Bob
