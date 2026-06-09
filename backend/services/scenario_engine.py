"""
Scenario Engine
Create and apply what-if scenarios to portfolios and risk models
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of scenarios"""
    MARKET_CRASH = "market_crash"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    CREDIT_SPREAD_WIDENING = "credit_spread_widening"
    COUNTERPARTY_DEFAULT = "counterparty_default"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CURRENCY_SHOCK = "currency_shock"
    COMMODITY_SHOCK = "commodity_shock"
    CUSTOM = "custom"


class Scenario:
    """Represents a risk scenario"""
    
    def __init__(
        self,
        scenario_id: str,
        name: str,
        scenario_type: ScenarioType,
        description: str,
        parameters: Dict[str, Any],
        severity: str = "medium"
    ):
        """
        Initialize scenario
        
        Args:
            scenario_id: Unique scenario identifier
            name: Scenario name
            scenario_type: Type of scenario
            description: Scenario description
            parameters: Scenario parameters
            severity: Severity level (low, medium, high, extreme)
        """
        self.scenario_id = scenario_id
        self.name = name
        self.scenario_type = scenario_type
        self.description = description
        self.parameters = parameters
        self.severity = severity
        self.created_at = datetime.utcnow().isoformat()


class ScenarioEngine:
    """Main scenario analysis engine"""
    
    def __init__(self):
        """Initialize scenario engine"""
        self.scenarios: Dict[str, Scenario] = {}
        self.scenario_results: Dict[str, Dict[str, Any]] = {}
        self.predefined_scenarios = self._create_predefined_scenarios()
        self.scenario_counter = 0
    
    def _create_predefined_scenarios(self) -> Dict[str, Scenario]:
        """Create predefined scenarios"""
        scenarios = {}
        
        # Market Crash Scenario
        scenarios['market_crash_2008'] = Scenario(
            scenario_id='market_crash_2008',
            name='2008 Financial Crisis',
            scenario_type=ScenarioType.MARKET_CRASH,
            description='Severe market downturn similar to 2008 financial crisis',
            parameters={
                'equity_shock': -0.40,  # 40% drop
                'credit_spread_widening': 0.05,  # 500 bps
                'volatility_increase': 2.5,
                'liquidity_reduction': 0.60,
                'correlation_increase': 0.30
            },
            severity='extreme'
        )
        
        # Interest Rate Shock
        scenarios['rate_shock_up'] = Scenario(
            scenario_id='rate_shock_up',
            name='Interest Rate Shock (Up)',
            scenario_type=ScenarioType.INTEREST_RATE_SHOCK,
            description='Sudden 200 bps increase in interest rates',
            parameters={
                'rate_change': 0.02,  # 200 bps
                'yield_curve_shift': 'parallel',
                'bond_price_impact': -0.15,
                'duration_effect': True
            },
            severity='high'
        )
        
        scenarios['rate_shock_down'] = Scenario(
            scenario_id='rate_shock_down',
            name='Interest Rate Shock (Down)',
            scenario_type=ScenarioType.INTEREST_RATE_SHOCK,
            description='Sudden 100 bps decrease in interest rates',
            parameters={
                'rate_change': -0.01,  # -100 bps
                'yield_curve_shift': 'parallel',
                'bond_price_impact': 0.08,
                'duration_effect': True
            },
            severity='medium'
        )
        
        # Credit Spread Widening
        scenarios['credit_crisis'] = Scenario(
            scenario_id='credit_crisis',
            name='Credit Spread Crisis',
            scenario_type=ScenarioType.CREDIT_SPREAD_WIDENING,
            description='Severe widening of credit spreads',
            parameters={
                'spread_widening_ig': 0.03,  # 300 bps for investment grade
                'spread_widening_hy': 0.08,  # 800 bps for high yield
                'default_rate_increase': 0.05,
                'recovery_rate_decrease': 0.15
            },
            severity='high'
        )
        
        # Counterparty Default
        scenarios['major_counterparty_default'] = Scenario(
            scenario_id='major_counterparty_default',
            name='Major Counterparty Default',
            scenario_type=ScenarioType.COUNTERPARTY_DEFAULT,
            description='Default of a major counterparty',
            parameters={
                'default_probability': 1.0,
                'recovery_rate': 0.40,
                'contagion_factor': 0.25,
                'market_impact': -0.10
            },
            severity='extreme'
        )
        
        # Liquidity Crisis
        scenarios['liquidity_crisis'] = Scenario(
            scenario_id='liquidity_crisis',
            name='Liquidity Crisis',
            scenario_type=ScenarioType.LIQUIDITY_CRISIS,
            description='Severe market liquidity shortage',
            parameters={
                'bid_ask_widening': 3.0,
                'market_depth_reduction': 0.70,
                'funding_cost_increase': 0.03,
                'asset_fire_sale_discount': 0.25
            },
            severity='high'
        )
        
        # Currency Shock
        scenarios['currency_crisis'] = Scenario(
            scenario_id='currency_crisis',
            name='Currency Crisis',
            scenario_type=ScenarioType.CURRENCY_SHOCK,
            description='Major currency devaluation',
            parameters={
                'fx_shock': -0.30,  # 30% devaluation
                'volatility_increase': 2.0,
                'cross_currency_correlation': 0.40
            },
            severity='high'
        )
        
        # Commodity Shock
        scenarios['oil_shock'] = Scenario(
            scenario_id='oil_shock',
            name='Oil Price Shock',
            scenario_type=ScenarioType.COMMODITY_SHOCK,
            description='Severe oil price spike',
            parameters={
                'oil_price_change': 0.80,  # 80% increase
                'energy_sector_impact': 0.30,
                'inflation_impact': 0.02,
                'economic_growth_impact': -0.015
            },
            severity='medium'
        )
        
        return scenarios
    
    def create_scenario(
        self,
        name: str,
        scenario_type: str,
        description: str,
        parameters: Dict[str, Any],
        severity: str = "medium"
    ) -> Scenario:
        """
        Create a new scenario
        
        Args:
            name: Scenario name
            scenario_type: Type of scenario
            description: Scenario description
            parameters: Scenario parameters
            severity: Severity level
            
        Returns:
            Created scenario
        """
        self.scenario_counter += 1
        scenario_id = f"SCN-{datetime.utcnow().strftime('%Y%m%d')}-{self.scenario_counter:04d}"
        
        try:
            s_type = ScenarioType[scenario_type.upper()]
        except KeyError:
            s_type = ScenarioType.CUSTOM
        
        scenario = Scenario(
            scenario_id=scenario_id,
            name=name,
            scenario_type=s_type,
            description=description,
            parameters=parameters,
            severity=severity
        )
        
        self.scenarios[scenario_id] = scenario
        logger.info(f"Created scenario: {scenario_id}")
        
        return scenario
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get a scenario by ID"""
        # Check custom scenarios first
        if scenario_id in self.scenarios:
            return self.scenarios[scenario_id]
        # Check predefined scenarios
        return self.predefined_scenarios.get(scenario_id)
    
    def list_scenarios(self, include_predefined: bool = True) -> List[Dict[str, Any]]:
        """
        List all scenarios
        
        Args:
            include_predefined: Include predefined scenarios
            
        Returns:
            List of scenario information
        """
        scenarios = []
        
        # Add custom scenarios
        for scenario in self.scenarios.values():
            scenarios.append({
                'scenario_id': scenario.scenario_id,
                'name': scenario.name,
                'type': scenario.scenario_type.value,
                'description': scenario.description,
                'severity': scenario.severity,
                'is_predefined': False,
                'created_at': scenario.created_at
            })
        
        # Add predefined scenarios
        if include_predefined:
            for scenario in self.predefined_scenarios.values():
                scenarios.append({
                    'scenario_id': scenario.scenario_id,
                    'name': scenario.name,
                    'type': scenario.scenario_type.value,
                    'description': scenario.description,
                    'severity': scenario.severity,
                    'is_predefined': True,
                    'created_at': scenario.created_at
                })
        
        return scenarios
    
    def apply_scenario(
        self,
        scenario_id: str,
        portfolio_data: Dict[str, Any],
        entity_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Apply scenario to portfolio
        
        Args:
            scenario_id: Scenario to apply
            portfolio_data: Portfolio data
            entity_data: Optional entity-level data
            
        Returns:
            Scenario impact results
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        logger.info(f"Applying scenario {scenario_id} to portfolio")
        
        # Calculate baseline metrics
        baseline_value = portfolio_data.get('total_value', 100000000)
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        
        # Apply scenario based on type
        if scenario.scenario_type == ScenarioType.MARKET_CRASH:
            impact = self._apply_market_crash(scenario, portfolio_data)
        elif scenario.scenario_type == ScenarioType.INTEREST_RATE_SHOCK:
            impact = self._apply_rate_shock(scenario, portfolio_data)
        elif scenario.scenario_type == ScenarioType.CREDIT_SPREAD_WIDENING:
            impact = self._apply_credit_shock(scenario, portfolio_data)
        elif scenario.scenario_type == ScenarioType.COUNTERPARTY_DEFAULT:
            impact = self._apply_counterparty_default(scenario, portfolio_data, entity_data)
        elif scenario.scenario_type == ScenarioType.LIQUIDITY_CRISIS:
            impact = self._apply_liquidity_crisis(scenario, portfolio_data)
        elif scenario.scenario_type == ScenarioType.CURRENCY_SHOCK:
            impact = self._apply_currency_shock(scenario, portfolio_data)
        elif scenario.scenario_type == ScenarioType.COMMODITY_SHOCK:
            impact = self._apply_commodity_shock(scenario, portfolio_data)
        else:
            impact = self._apply_custom_scenario(scenario, portfolio_data)
        
        # Calculate summary metrics
        result = {
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'scenario_type': scenario.scenario_type.value,
            'severity': scenario.severity,
            'baseline': {
                'portfolio_value': baseline_value,
                'risk_score': baseline_risk
            },
            'stressed': {
                'portfolio_value': impact['portfolio_value'],
                'risk_score': impact['risk_score']
            },
            'impact': {
                'value_change': impact['portfolio_value'] - baseline_value,
                'value_change_pct': ((impact['portfolio_value'] - baseline_value) / baseline_value) * 100,
                'risk_change': impact['risk_score'] - baseline_risk,
                'risk_change_pct': ((impact['risk_score'] - baseline_risk) / baseline_risk) * 100 if baseline_risk > 0 else 0
            },
            'details': impact.get('details', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store result
        self.scenario_results[f"{scenario_id}_{datetime.utcnow().timestamp()}"] = result
        
        return result
    
    def _apply_market_crash(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply market crash scenario"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        # Calculate equity impact
        equity_shock = params.get('equity_shock', -0.30)
        equity_exposure = portfolio_data.get('equity_exposure', 0.60)
        
        # Calculate credit impact
        credit_spread = params.get('credit_spread_widening', 0.03)
        credit_exposure = portfolio_data.get('credit_exposure', 0.30)
        
        # Calculate total impact
        value_impact = (
            baseline_value * equity_exposure * equity_shock +
            baseline_value * credit_exposure * (-credit_spread * 5)  # Approximate duration impact
        )
        
        new_value = baseline_value + value_impact
        
        # Risk score increases
        volatility_increase = params.get('volatility_increase', 2.0)
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = min(1.0, baseline_risk * volatility_increase)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': {
                'equity_impact': baseline_value * equity_exposure * equity_shock,
                'credit_impact': baseline_value * credit_exposure * (-credit_spread * 5),
                'volatility_multiplier': volatility_increase
            }
        }
    
    def _apply_rate_shock(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply interest rate shock"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        rate_change = params.get('rate_change', 0.02)
        duration = portfolio_data.get('duration', 5.0)
        bond_exposure = portfolio_data.get('bond_exposure', 0.40)
        
        # Duration-based impact
        bond_impact = -duration * rate_change * baseline_value * bond_exposure
        
        new_value = baseline_value + bond_impact
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = baseline_risk * (1 + abs(rate_change) * 10)
        
        return {
            'portfolio_value': new_value,
            'risk_score': min(1.0, new_risk),
            'details': {
                'rate_change_bps': rate_change * 10000,
                'duration': duration,
                'bond_impact': bond_impact
            }
        }
    
    def _apply_credit_shock(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply credit spread widening"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        spread_widening = params.get('spread_widening_ig', 0.02)
        credit_exposure = portfolio_data.get('credit_exposure', 0.30)
        duration = portfolio_data.get('duration', 5.0)
        
        credit_impact = -spread_widening * duration * baseline_value * credit_exposure
        
        new_value = baseline_value + credit_impact
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = baseline_risk * 1.5
        
        return {
            'portfolio_value': new_value,
            'risk_score': min(1.0, new_risk),
            'details': {
                'spread_widening_bps': spread_widening * 10000,
                'credit_impact': credit_impact
            }
        }
    
    def _apply_counterparty_default(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any],
        entity_data: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Apply counterparty default"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        # Assume largest counterparty defaults
        if entity_data:
            largest_exposure = max([e.get('exposure', 0) for e in entity_data])
        else:
            largest_exposure = baseline_value * 0.10  # Assume 10% concentration
        
        recovery_rate = params.get('recovery_rate', 0.40)
        loss = largest_exposure * (1 - recovery_rate)
        
        # Contagion effect
        contagion = params.get('contagion_factor', 0.20)
        contagion_loss = baseline_value * contagion * 0.05
        
        total_loss = loss + contagion_loss
        new_value = baseline_value - total_loss
        
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = min(1.0, baseline_risk * 2.0)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': {
                'direct_loss': loss,
                'contagion_loss': contagion_loss,
                'total_loss': total_loss,
                'recovery_rate': recovery_rate
            }
        }
    
    def _apply_liquidity_crisis(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply liquidity crisis"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        fire_sale_discount = params.get('asset_fire_sale_discount', 0.20)
        illiquid_portion = portfolio_data.get('illiquid_assets', 0.30)
        
        liquidity_loss = baseline_value * illiquid_portion * fire_sale_discount
        
        new_value = baseline_value - liquidity_loss
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = min(1.0, baseline_risk * 1.8)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': {
                'fire_sale_discount': fire_sale_discount,
                'illiquid_portion': illiquid_portion,
                'liquidity_loss': liquidity_loss
            }
        }
    
    def _apply_currency_shock(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply currency shock"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        fx_shock = params.get('fx_shock', -0.20)
        fx_exposure = portfolio_data.get('fx_exposure', 0.25)
        
        fx_impact = baseline_value * fx_exposure * fx_shock
        
        new_value = baseline_value + fx_impact
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = min(1.0, baseline_risk * 1.4)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': {
                'fx_shock_pct': fx_shock * 100,
                'fx_exposure': fx_exposure,
                'fx_impact': fx_impact
            }
        }
    
    def _apply_commodity_shock(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply commodity shock"""
        params = scenario.parameters
        baseline_value = portfolio_data.get('total_value', 100000000)
        
        commodity_change = params.get('oil_price_change', 0.50)
        commodity_exposure = portfolio_data.get('commodity_exposure', 0.10)
        
        commodity_impact = baseline_value * commodity_exposure * commodity_change
        
        new_value = baseline_value + commodity_impact
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        new_risk = min(1.0, baseline_risk * 1.3)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': {
                'commodity_change_pct': commodity_change * 100,
                'commodity_exposure': commodity_exposure,
                'commodity_impact': commodity_impact
            }
        }
    
    def _apply_custom_scenario(
        self,
        scenario: Scenario,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom scenario"""
        baseline_value = portfolio_data.get('total_value', 100000000)
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        
        # Use generic shock parameters
        params = scenario.parameters
        value_shock = params.get('value_shock', -0.10)
        risk_multiplier = params.get('risk_multiplier', 1.5)
        
        new_value = baseline_value * (1 + value_shock)
        new_risk = min(1.0, baseline_risk * risk_multiplier)
        
        return {
            'portfolio_value': new_value,
            'risk_score': new_risk,
            'details': params
        }
    
    def compare_scenarios(
        self,
        scenario_ids: List[str],
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios
        
        Args:
            scenario_ids: List of scenario IDs to compare
            portfolio_data: Portfolio data
            
        Returns:
            Comparison results
        """
        results = []
        
        for scenario_id in scenario_ids:
            result = self.apply_scenario(scenario_id, portfolio_data)
            results.append(result)
        
        # Find worst case
        worst_case = min(results, key=lambda x: x['stressed']['portfolio_value'])
        best_case = max(results, key=lambda x: x['stressed']['portfolio_value'])
        
        return {
            'scenarios': results,
            'worst_case': worst_case,
            'best_case': best_case,
            'comparison_date': datetime.utcnow().isoformat()
        }


# Global scenario engine instance
_scenario_engine = None


def get_scenario_engine() -> ScenarioEngine:
    """Get or create global scenario engine instance"""
    global _scenario_engine
    if _scenario_engine is None:
        _scenario_engine = ScenarioEngine()
    return _scenario_engine


# Made with Bob