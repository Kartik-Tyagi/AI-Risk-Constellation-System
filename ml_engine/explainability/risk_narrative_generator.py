"""
Risk Narrative Generator
Generates natural language explanations for risk predictions
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RiskNarrativeGenerator:
    """Generate natural language explanations for risk assessments"""
    
    def __init__(self):
        """Initialize narrative generator"""
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load narrative templates"""
        return {
            'high_risk': [
                "The entity {entity_id} shows a high risk level of {risk_score:.2f}. ",
                "Analysis indicates elevated risk for {entity_id} with a score of {risk_score:.2f}. ",
                "{entity_id} is classified as high risk ({risk_score:.2f}). "
            ],
            'medium_risk': [
                "The entity {entity_id} has a moderate risk level of {risk_score:.2f}. ",
                "{entity_id} shows medium risk with a score of {risk_score:.2f}. "
            ],
            'low_risk': [
                "The entity {entity_id} demonstrates low risk at {risk_score:.2f}. ",
                "{entity_id} is classified as low risk ({risk_score:.2f}). "
            ],
            'top_factors': [
                "The primary risk factors are: {factors}. ",
                "Key contributors include: {factors}. ",
                "Main risk drivers: {factors}. "
            ],
            'correlation': [
                "This entity shows strong correlation with {correlated_entities}. ",
                "Significant relationships exist with {correlated_entities}. "
            ],
            'cascade': [
                "A failure could impact {affected_count} connected entities. ",
                "Risk propagation analysis shows potential cascade affecting {affected_count} entities. "
            ],
            'trend': [
                "Risk has been {trend} over the past period. ",
                "The trend shows {trend} risk levels. "
            ],
            'recommendation': [
                "Recommended action: {action}. ",
                "Consider: {action}. "
            ]
        }
    
    def generate_explanation(
        self,
        risk_data: Dict[str, Any],
        shap_explanation: Optional[Dict[str, Any]] = None,
        attention_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate comprehensive risk explanation
        
        Args:
            risk_data: Risk assessment data
            shap_explanation: SHAP explanation (optional)
            attention_data: Attention weights (optional)
            
        Returns:
            Natural language explanation
        """
        narrative_parts = []
        
        # Risk level introduction
        risk_level = self._get_risk_level(risk_data.get('risk_score', 0))
        narrative_parts.append(
            self.templates[risk_level][0].format(
                entity_id=risk_data.get('entity_id', 'Unknown'),
                risk_score=risk_data.get('risk_score', 0)
            )
        )
        
        # Top risk factors from SHAP
        if shap_explanation and 'top_features' in shap_explanation:
            top_features = shap_explanation['top_features'][:3]
            factors_text = ', '.join([f"{f['feature']} ({f['shap_value']:.2f})" for f in top_features])
            narrative_parts.append(
                self.templates['top_factors'][0].format(factors=factors_text)
            )
        
        # Correlation information
        if risk_data.get('correlated_entities'):
            correlated = ', '.join(risk_data['correlated_entities'][:3])
            narrative_parts.append(
                self.templates['correlation'][0].format(correlated_entities=correlated)
            )
        
        # Cascade potential
        if risk_data.get('cascade_potential'):
            affected_count = risk_data['cascade_potential'].get('affected_entities', 0)
            narrative_parts.append(
                self.templates['cascade'][0].format(affected_count=affected_count)
            )
        
        # Trend information
        if risk_data.get('trend'):
            narrative_parts.append(
                self.templates['trend'][0].format(trend=risk_data['trend'])
            )
        
        # Recommendations
        if risk_data.get('recommendations'):
            for rec in risk_data['recommendations'][:2]:
                narrative_parts.append(
                    self.templates['recommendation'][0].format(action=rec)
                )
        
        return ''.join(narrative_parts)
    
    def generate_comparison_narrative(
        self,
        entity1_data: Dict[str, Any],
        entity2_data: Dict[str, Any]
    ) -> str:
        """Generate narrative comparing two entities"""
        entity1_id = entity1_data.get('entity_id', 'Entity 1')
        entity2_id = entity2_data.get('entity_id', 'Entity 2')
        score1 = entity1_data.get('risk_score', 0)
        score2 = entity2_data.get('risk_score', 0)
        
        if score1 > score2:
            higher, lower = entity1_id, entity2_id
            diff = score1 - score2
        else:
            higher, lower = entity2_id, entity1_id
            diff = score2 - score1
        
        narrative = f"Comparing {entity1_id} (risk: {score1:.2f}) and {entity2_id} (risk: {score2:.2f}). "
        narrative += f"{higher} shows higher risk than {lower} by {diff:.2f} points. "
        
        return narrative
    
    def generate_cascade_narrative(self, cascade_data: Dict[str, Any]) -> str:
        """Generate narrative for cascade analysis"""
        source = cascade_data.get('source_entity', 'Unknown')
        affected = cascade_data.get('affected_entities', [])
        depth = cascade_data.get('cascade_depth', 0)
        
        narrative = f"Risk cascade analysis from {source}: "
        narrative += f"Potential impact on {len(affected)} entities across {depth} propagation levels. "
        
        if affected:
            top_affected = ', '.join([e['id'] for e in affected[:3]])
            narrative += f"Most affected entities: {top_affected}. "
        
        return narrative
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= 75:
            return 'high_risk'
        elif risk_score >= 40:
            return 'medium_risk'
        else:
            return 'low_risk'


def create_narrative_generator() -> RiskNarrativeGenerator:
    """Factory function to create narrative generator"""
    return RiskNarrativeGenerator()


# Made with Bob