"""
Entity Pydantic Models
Request and response models for entity/counterparty endpoints
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class EntityBase(BaseModel):
    """Base entity model"""
    entity_id: str = Field(..., description="Unique entity identifier")
    entity_name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type (corporation/bank/fund/government)")
    sector: Optional[str] = Field(None, description="Industry sector")
    country: Optional[str] = Field(None, description="Country of incorporation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_id": "ENT001",
                "entity_name": "Tech Corp",
                "entity_type": "corporation",
                "sector": "technology",
                "country": "USA"
            }
        }


class EntityCreate(EntityBase):
    """Request model for creating an entity"""
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Entity relationships")


class EntityUpdate(BaseModel):
    """Request model for updating an entity"""
    entity_name: Optional[str] = Field(None, description="Entity name")
    entity_type: Optional[str] = Field(None, description="Entity type")
    sector: Optional[str] = Field(None, description="Industry sector")
    country: Optional[str] = Field(None, description="Country")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EntityRelationship(BaseModel):
    """Entity relationship"""
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Relationship type")
    strength: float = Field(..., description="Relationship strength (0-1)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Relationship metadata")


class EntityResponse(EntityBase):
    """Response model for entity"""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    relationships: List[EntityRelationship] = Field(default_factory=list, description="Entity relationships")
    risk_score: Optional[float] = Field(None, description="Current risk score")
    risk_level: Optional[str] = Field(None, description="Current risk level")


class EntityListResponse(BaseModel):
    """Response model for entity list"""
    entities: List[EntityResponse] = Field(..., description="List of entities")
    total: int = Field(..., description="Total number of entities")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Page size")


class EntitySearchRequest(BaseModel):
    """Request model for entity search"""
    query: str = Field(..., description="Search query")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    sector: Optional[str] = Field(None, description="Filter by sector")
    country: Optional[str] = Field(None, description="Filter by country")
    risk_level: Optional[str] = Field(None, description="Filter by risk level")
    limit: int = Field(default=20, description="Maximum results")


class EntityNetworkRequest(BaseModel):
    """Request model for entity network"""
    entity_id: str = Field(..., description="Central entity ID")
    depth: int = Field(default=2, description="Network depth")
    relationship_types: Optional[List[str]] = Field(None, description="Filter by relationship types")
    min_strength: float = Field(default=0.0, description="Minimum relationship strength")


class EntityNetworkNode(BaseModel):
    """Node in entity network"""
    entity_id: str = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type")
    risk_score: Optional[float] = Field(None, description="Risk score")
    distance: int = Field(..., description="Distance from central entity")


class EntityNetworkEdge(BaseModel):
    """Edge in entity network"""
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Relationship type")
    strength: float = Field(..., description="Relationship strength")


class EntityNetworkResponse(BaseModel):
    """Response model for entity network"""
    central_entity_id: str = Field(..., description="Central entity ID")
    nodes: List[EntityNetworkNode] = Field(..., description="Network nodes")
    edges: List[EntityNetworkEdge] = Field(..., description="Network edges")
    statistics: Dict[str, Any] = Field(..., description="Network statistics")

# Made with Bob
