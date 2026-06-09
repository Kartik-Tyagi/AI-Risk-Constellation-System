"""
Explainability API Routes
Endpoints for AI explainability features
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
import sys
import os

# Add ml_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ml_engine.explainability.shap_explainer import SHAPExplainer
from ml_engine.explainability.attention_visualizer import AttentionVisualizer
from ml_engine.explainability.risk_narrative_generator import RiskNarrativeGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/explainability", tags=["explainability"])

# Initialize explainability components (will be replaced with actual models)
shap_explainer = None
attention_visualizer = None
narrative_generator = None

# Mock model for development (replace with actual trained model)
class MockModel:
    def predict(self, X):
        import numpy as np
        return np.array([np.mean(X) * 100])

def get_shap_explainer():
    """Get or create SHAP explainer"""
    global shap_explainer
    if shap_explainer is None:
        # Initialize with mock model and feature names
        mock_model = MockModel()
        feature_names = ['volatility', 'correlation', 'exposure', 'liquidity', 'credit_rating']
        shap_explainer = SHAPExplainer(mock_model, feature_names)
    return shap_explainer


def get_attention_visualizer():
    """Get or create attention visualizer"""
    global attention_visualizer
    if attention_visualizer is None:
        # Initialize with mock GAT model
        mock_gat_model = MockModel()
        attention_visualizer = AttentionVisualizer(mock_gat_model)
    return attention_visualizer


def get_narrative_generator():
    """Get or create narrative generator"""
    global narrative_generator
    if narrative_generator is None:
        narrative_generator = RiskNarrativeGenerator()
    return narrative_generator


@router.get("/explain/risk/{entity_id}")
async def explain_risk(
    entity_id: str,
    include_narrative: bool = True,
    include_attention: bool = False
) -> Dict[str, Any]:
    """
    Get comprehensive explanation for entity risk
    
    Args:
        entity_id: Entity identifier
        include_narrative: Include natural language explanation
        include_attention: Include attention weights
        
    Returns:
        Explanation data
    """
    try:
        # Mock risk data (in production, fetch from database)
        risk_data = {
            'entity_id': entity_id,
            'risk_score': 72.5,
            'correlated_entities': ['ENT-002', 'ENT-003'],
            'cascade_potential': {'affected_entities': 15},
            'trend': 'increasing',
            'recommendations': ['Increase monitoring', 'Review exposure limits']
        }
        
        # Mock features for SHAP (in production, get from model)
        import numpy as np
        features = np.array([0.45, 0.78, 0.62, 0.33, 0.55])
        
        explainer = get_shap_explainer()
        
        # Generate SHAP explanation
        shap_explanation = explainer.explain_prediction(
            features=features,
            entity_id=entity_id
        )
        
        response = {
            'entity_id': entity_id,
            'risk_score': risk_data['risk_score'],
            'shap_explanation': shap_explanation,
            'risk_data': risk_data
        }
        
        # Add narrative if requested
        if include_narrative:
            generator = get_narrative_generator()
            narrative = generator.generate_explanation(
                risk_data=risk_data,
                shap_explanation=shap_explanation
            )
            response['narrative'] = narrative
        
        # Add attention weights if requested
        if include_attention:
            visualizer = get_attention_visualizer()
            # Mock attention data (in production, get from GAT model)
            mock_graph_data = {
                'node_features': np.random.randn(10, 5),
                'edge_index': np.array([[0, 1, 2], [1, 2, 3]]),
                'node_ids': [f'ENT-{i:03d}' for i in range(10)]
            }
            attention_data = visualizer.get_node_attention_summary(
                graph_data=mock_graph_data,
                node_id=entity_id
            )
            response['attention'] = attention_data
        
        return response
        
    except Exception as e:
        logger.error(f"Error explaining risk for {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/prediction/{prediction_id}")
async def explain_prediction(prediction_id: str) -> Dict[str, Any]:
    """
    Get explanation for a specific prediction
    
    Args:
        prediction_id: Prediction identifier
        
    Returns:
        Prediction explanation
    """
    try:
        # Mock prediction data
        prediction_data = {
            'prediction_id': prediction_id,
            'entity_id': 'ENT-001',
            'predicted_risk': 68.3,
            'confidence': 0.87,
            'timestamp': '2026-06-09T07:30:00Z'
        }
        
        # Mock features
        import numpy as np
        features = np.array([0.42, 0.71, 0.58, 0.39, 0.61])
        
        explainer = get_shap_explainer()
        shap_explanation = explainer.explain_prediction(
            features=features,
            entity_id=prediction_data['entity_id']
        )
        
        return {
            'prediction': prediction_data,
            'explanation': shap_explanation,
            'force_plot_data': explainer.generate_force_plot_data(
                features=features,
                entity_id=prediction_data['entity_id']
            )
        }
        
    except Exception as e:
        logger.error(f"Error explaining prediction {prediction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/attention/{graph_id}")
async def explain_attention(
    graph_id: str,
    source_node: Optional[str] = None,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Get attention weight explanations for graph
    
    Args:
        graph_id: Graph identifier
        source_node: Optional source node for flow visualization
        depth: Depth for attention flow
        
    Returns:
        Attention explanations
    """
    try:
        visualizer = get_attention_visualizer()
        
        # Mock graph data (in production, get from GAT model)
        import numpy as np
        graph_data = {
            'node_features': np.random.randn(10, 5),
            'edge_index': np.array([[0, 1, 2, 3], [1, 2, 3, 4]]),
            'node_ids': [f'ENT-{i:03d}' for i in range(10)]
        }
        
        # Get top attention edges
        top_edges = visualizer.get_top_attention_edges(
            graph_data=graph_data,
            top_k=10
        )
        
        response = {
            'graph_id': graph_id,
            'top_attention_edges': top_edges
        }
        
        # Add attention flow if source node specified
        if source_node:
            flow_data = visualizer.visualize_attention_flow(
                graph_data=graph_data,
                source_node=source_node,
                max_depth=depth
            )
            response['attention_flow'] = flow_data
        
        return response
        
    except Exception as e:
        logger.error(f"Error explaining attention for {graph_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/compare")
async def compare_entities(
    entity_ids: List[str],
    include_narrative: bool = True
) -> Dict[str, Any]:
    """
    Compare explanations for multiple entities
    
    Args:
        entity_ids: List of entity IDs to compare
        include_narrative: Include comparison narrative
        
    Returns:
        Comparison data
    """
    try:
        if len(entity_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 entities required for comparison"
            )
        
        explainer = get_shap_explainer()
        comparisons = []
        
        import numpy as np
        for entity_id in entity_ids:
            # Mock data for each entity
            features = np.array([
                0.40 + (hash(entity_id) % 20) / 100,
                0.70 + (hash(entity_id) % 15) / 100,
                0.55 + (hash(entity_id) % 25) / 100,
                0.35 + (hash(entity_id) % 30) / 100,
                0.60 + (hash(entity_id) % 20) / 100
            ])
            
            risk_score = float(np.mean(features) * 100)
            
            explanation = explainer.explain_prediction(
                features=features,
                entity_id=entity_id
            )
            
            comparisons.append({
                'entity_id': entity_id,
                'risk_score': risk_score,
                'explanation': explanation
            })
        
        response: Dict[str, Any] = {'comparisons': comparisons}
        
        # Add narrative comparison
        if include_narrative and len(comparisons) >= 2:
            generator = get_narrative_generator()
            narrative = generator.generate_comparison_narrative(
                entity1_data={'entity_id': comparisons[0]['entity_id'],
                             'risk_score': comparisons[0]['risk_score']},
                entity2_data={'entity_id': comparisons[1]['entity_id'],
                             'risk_score': comparisons[1]['risk_score']}
            )
            response['narrative'] = narrative
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing entities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/cascade/{entity_id}")
async def explain_cascade(
    entity_id: str,
    include_narrative: bool = True
) -> Dict[str, Any]:
    """
    Explain cascade/contagion effects from entity
    
    Args:
        entity_id: Source entity ID
        include_narrative: Include narrative explanation
        
    Returns:
        Cascade explanation
    """
    try:
        # Mock cascade data
        cascade_data = {
            'source_entity': entity_id,
            'affected_entities': [
                {'id': 'ENT-002', 'impact': 0.75},
                {'id': 'ENT-003', 'impact': 0.62},
                {'id': 'ENT-004', 'impact': 0.48}
            ],
            'cascade_depth': 3,
            'total_impact': 1.85
        }
        
        response: Dict[str, Any] = {'cascade_data': cascade_data}
        
        if include_narrative:
            generator = get_narrative_generator()
            narrative = generator.generate_cascade_narrative(cascade_data)
            response['narrative'] = narrative
        
        return response
        
    except Exception as e:
        logger.error(f"Error explaining cascade for {entity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Made with Bob