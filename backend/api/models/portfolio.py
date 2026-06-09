"""
Portfolio Pydantic Models
Request and response models for portfolio endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class PortfolioPosition(BaseModel):
    """Individual position in a portfolio"""
    entity_id: str = Field(..., description="Entity/counterparty ID")
    entity_name: str = Field(..., description="Entity name")
    position_type: str = Field(..., description="Position type (long/short)")
    quantity: float = Field(..., description="Position quantity")
    market_value: float = Field(..., description="Current market value")
    currency: str = Field(default="USD", description="Currency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "entity_name": "Tech Corp",
                "position_type": "long",
                "quantity": 1000,
                "market_value": 150000.0,
                "currency": "USD"
            }
        }


class PortfolioCreate(BaseModel):
    """Request model for creating a portfolio"""
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    positions: List[PortfolioPosition] = Field(..., description="Portfolio positions")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('positions')
    def validate_positions(cls, v):
        if not v:
            raise ValueError("Portfolio must have at least one position")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tech Portfolio",
                "description": "Technology sector investments",
                "positions": [
                    {
                        "entity_id": "ENT001",
                        "entity_name": "Tech Corp",
                        "position_type": "long",
                        "quantity": 1000,
                        "market_value": 150000.0,
                        "currency": "USD"
                    }
                ],
                "metadata": {
                    "strategy": "growth",
                    "risk_tolerance": "moderate"
                }
            }
        }


class PortfolioUpdate(BaseModel):
    """Request model for updating a portfolio"""
    name: Optional[str] = Field(None, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    positions: Optional[List[PortfolioPosition]] = Field(None, description="Portfolio positions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PortfolioResponse(BaseModel):
    """Response model for portfolio"""
    portfolio_id: str = Field(..., description="Portfolio ID")
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    positions: List[PortfolioPosition] = Field(..., description="Portfolio positions")
    total_value: float = Field(..., description="Total portfolio value")
    position_count: int = Field(..., description="Number of positions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "PORT001",
                "name": "Tech Portfolio",
                "description": "Technology sector investments",
                "positions": [
                    {
                        "entity_id": "ENT001",
                        "entity_name": "Tech Corp",
                        "position_type": "long",
                        "quantity": 1000,
                        "market_value": 150000.0,
                        "currency": "USD"
                    }
                ],
                "total_value": 150000.0,
                "position_count": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "metadata": {
                    "strategy": "growth",
                    "risk_tolerance": "moderate"
                }
            }
        }


class PortfolioListResponse(BaseModel):
    """Response model for portfolio list"""
    portfolios: List[PortfolioResponse] = Field(..., description="List of portfolios")
    total: int = Field(..., description="Total number of portfolios")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Page size")


class PortfolioRiskMetrics(BaseModel):
    """Portfolio risk metrics"""
    var_95: float = Field(..., description="Value at Risk (95%)")
    var_99: float = Field(..., description="Value at Risk (99%)")
    cvar_95: float = Field(..., description="Conditional VaR (95%)")
    expected_shortfall: float = Field(..., description="Expected shortfall")
    volatility: float = Field(..., description="Portfolio volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    beta: float = Field(..., description="Portfolio beta")


class PortfolioRiskResponse(BaseModel):
    """Response model for portfolio risk analysis"""
    portfolio_id: str = Field(..., description="Portfolio ID")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    risk_metrics: PortfolioRiskMetrics = Field(..., description="Risk metrics")
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")
    risk_dna: Dict[str, float] = Field(..., description="Risk DNA fingerprint")
    top_risks: List[Dict[str, Any]] = Field(..., description="Top risk contributors")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "PORT001",
                "timestamp": "2024-01-01T00:00:00Z",
                "risk_metrics": {
                    "var_95": 15000.0,
                    "var_99": 25000.0,
                    "cvar_95": 30000.0,
                    "expected_shortfall": 35000.0,
                    "volatility": 0.25,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": 0.15,
                    "beta": 1.2
                },
                "risk_score": 65.5,
                "risk_level": "medium",
                "risk_dna": {
                    "market_risk": 0.4,
                    "credit_risk": 0.3,
                    "liquidity_risk": 0.2,
                    "operational_risk": 0.1
                },
                "top_risks": [
                    {
                        "entity_id": "ENT001",
                        "entity_name": "Tech Corp",
                        "risk_contribution": 0.45,
                        "risk_type": "market_risk"
                    }
                ],
                "recommendations": [
                    "Consider diversifying technology sector exposure",
                    "Monitor credit risk for ENT001"
                ]
            }
        }


class PortfolioOptimizationRequest(BaseModel):
    """Request model for portfolio optimization"""
    portfolio_id: str = Field(..., description="Portfolio ID")
    objective: str = Field(..., description="Optimization objective (minimize_risk/maximize_return/sharpe)")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Optimization constraints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "PORT001",
                "objective": "minimize_risk",
                "constraints": {
                    "max_position_weight": 0.2,
                    "min_return": 0.08,
                    "max_volatility": 0.15
                }
            }
        }


class PortfolioOptimizationResponse(BaseModel):
    """Response model for portfolio optimization"""
    portfolio_id: str = Field(..., description="Portfolio ID")
    optimized_positions: List[PortfolioPosition] = Field(..., description="Optimized positions")
    expected_return: float = Field(..., description="Expected return")
    expected_risk: float = Field(..., description="Expected risk")
    sharpe_ratio: float = Field(..., description="Expected Sharpe ratio")
    changes: List[Dict[str, Any]] = Field(..., description="Recommended changes")

# Made with Bob
