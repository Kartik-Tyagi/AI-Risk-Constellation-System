"""
Stress Testing Service
Advanced stress testing with historical scenarios, Monte Carlo simulation, and custom tests
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class StressTest:
    """Represents a stress test"""
    
    def __init__(
        self,
        test_id: str,
        name: str,
        test_type: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        """
        Initialize stress test
        
        Args:
            test_id: Unique test identifier
            name: Test name
            test_type: Type of test (historical, monte_carlo, custom)
            description: Test description
            parameters: Test parameters
        """
        self.test_id = test_id
        self.name = name
        self.test_type = test_type
        self.description = description
        self.parameters = parameters
        self.created_at = datetime.utcnow().isoformat()


class StressTestingService:
    """Main stress testing service"""
    
    def __init__(self):
        """Initialize stress testing service"""
        self.stress_tests: Dict[str, StressTest] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.test_counter = 0
        self.historical_scenarios = self._create_historical_scenarios()
    
    def _create_historical_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create historical stress scenarios"""
        return {
            'black_monday_1987': {
                'name': 'Black Monday 1987',
                'date': '1987-10-19',
                'equity_shock': -0.22,
                'volatility_spike': 3.5,
                'duration': 1  # days
            },
            'ltcm_crisis_1998': {
                'name': 'LTCM Crisis 1998',
                'date': '1998-08-17',
                'equity_shock': -0.15,
                'credit_spread': 0.04,
                'liquidity_crisis': True,
                'duration': 30
            },
            'dot_com_crash_2000': {
                'name': 'Dot-com Crash 2000-2002',
                'date': '2000-03-10',
                'equity_shock': -0.49,
                'tech_sector_shock': -0.78,
                'duration': 730
            },
            'financial_crisis_2008': {
                'name': 'Financial Crisis 2008',
                'date': '2008-09-15',
                'equity_shock': -0.57,
                'credit_spread': 0.06,
                'counterparty_risk': 0.80,
                'liquidity_crisis': True,
                'duration': 180
            },
            'flash_crash_2010': {
                'name': 'Flash Crash 2010',
                'date': '2010-05-06',
                'equity_shock': -0.09,
                'volatility_spike': 5.0,
                'liquidity_evaporation': True,
                'duration': 0.25  # hours
            },
            'european_debt_crisis_2011': {
                'name': 'European Debt Crisis 2011',
                'date': '2011-08-08',
                'equity_shock': -0.18,
                'sovereign_spread': 0.05,
                'currency_volatility': 2.0,
                'duration': 90
            },
            'covid_crash_2020': {
                'name': 'COVID-19 Crash 2020',
                'date': '2020-03-16',
                'equity_shock': -0.34,
                'volatility_spike': 4.0,
                'credit_spread': 0.03,
                'liquidity_crisis': True,
                'duration': 30
            }
        }
    
    def create_stress_test(
        self,
        name: str,
        test_type: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> StressTest:
        """
        Create a new stress test
        
        Args:
            name: Test name
            test_type: Type of test
            description: Test description
            parameters: Test parameters
            
        Returns:
            Created stress test
        """
        self.test_counter += 1
        test_id = f"ST-{datetime.utcnow().strftime('%Y%m%d')}-{self.test_counter:04d}"
        
        test = StressTest(
            test_id=test_id,
            name=name,
            test_type=test_type,
            description=description,
            parameters=parameters
        )
        
        self.stress_tests[test_id] = test
        logger.info(f"Created stress test: {test_id}")
        
        return test
    
    def run_historical_stress_test(
        self,
        scenario_key: str,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run historical stress test
        
        Args:
            scenario_key: Historical scenario key
            portfolio_data: Portfolio data
            
        Returns:
            Stress test results
        """
        if scenario_key not in self.historical_scenarios:
            raise ValueError(f"Historical scenario {scenario_key} not found")
        
        scenario = self.historical_scenarios[scenario_key]
        baseline_value = portfolio_data.get('total_value', 100000000)
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        
        logger.info(f"Running historical stress test: {scenario['name']}")
        
        # Calculate impacts
        equity_impact = 0
        if 'equity_shock' in scenario:
            equity_exposure = portfolio_data.get('equity_exposure', 0.60)
            equity_impact = baseline_value * equity_exposure * scenario['equity_shock']
        
        credit_impact = 0
        if 'credit_spread' in scenario:
            credit_exposure = portfolio_data.get('credit_exposure', 0.30)
            duration = portfolio_data.get('duration', 5.0)
            credit_impact = -scenario['credit_spread'] * duration * baseline_value * credit_exposure
        
        liquidity_impact = 0
        if scenario.get('liquidity_crisis'):
            illiquid_assets = portfolio_data.get('illiquid_assets', 0.20)
            liquidity_impact = -baseline_value * illiquid_assets * 0.15
        
        total_impact = equity_impact + credit_impact + liquidity_impact
        stressed_value = baseline_value + total_impact
        
        # Calculate stressed risk
        volatility_multiplier = scenario.get('volatility_spike', 2.0)
        stressed_risk = min(1.0, baseline_risk * volatility_multiplier)
        
        result = {
            'test_type': 'historical',
            'scenario': scenario['name'],
            'scenario_date': scenario['date'],
            'baseline': {
                'portfolio_value': baseline_value,
                'risk_score': baseline_risk
            },
            'stressed': {
                'portfolio_value': stressed_value,
                'risk_score': stressed_risk
            },
            'impact': {
                'total_loss': total_impact,
                'loss_percentage': (total_impact / baseline_value) * 100,
                'equity_impact': equity_impact,
                'credit_impact': credit_impact,
                'liquidity_impact': liquidity_impact
            },
            'duration_days': scenario.get('duration', 1),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def run_monte_carlo_simulation(
        self,
        portfolio_data: Dict[str, Any],
        num_simulations: int = 10000,
        time_horizon_days: int = 252,
        confidence_levels: List[float] = [0.95, 0.99]
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation
        
        Args:
            portfolio_data: Portfolio data
            num_simulations: Number of simulations
            time_horizon_days: Time horizon in days
            confidence_levels: Confidence levels for VaR
            
        Returns:
            Simulation results
        """
        logger.info(f"Running Monte Carlo simulation with {num_simulations} paths")
        
        baseline_value = portfolio_data.get('total_value', 100000000)
        expected_return = portfolio_data.get('expected_return', 0.08)
        volatility = portfolio_data.get('volatility', 0.15)
        
        # Time parameters
        dt = time_horizon_days / 252  # Convert to years
        
        # Generate random returns
        np.random.seed(42)  # For reproducibility
        random_returns = np.random.normal(
            expected_return * dt,
            volatility * np.sqrt(dt),
            num_simulations
        )
        
        # Calculate portfolio values
        simulated_values = baseline_value * (1 + random_returns)
        simulated_returns = random_returns
        
        # Calculate statistics
        mean_value = np.mean(simulated_values)
        median_value = np.median(simulated_values)
        std_value = np.std(simulated_values)
        
        # Calculate VaR and CVaR
        var_results = {}
        cvar_results = {}
        
        for confidence in confidence_levels:
            var_percentile = (1 - confidence) * 100
            var_value = np.percentile(simulated_values, var_percentile)
            var_loss = baseline_value - var_value
            
            # CVaR (Expected Shortfall)
            tail_losses = simulated_values[simulated_values <= var_value]
            cvar_value = np.mean(tail_losses) if len(tail_losses) > 0 else var_value
            cvar_loss = baseline_value - cvar_value
            
            var_results[f'var_{int(confidence*100)}'] = {
                'value': var_value,
                'loss': var_loss,
                'loss_percentage': (var_loss / baseline_value) * 100
            }
            
            cvar_results[f'cvar_{int(confidence*100)}'] = {
                'value': cvar_value,
                'loss': cvar_loss,
                'loss_percentage': (cvar_loss / baseline_value) * 100
            }
        
        # Calculate percentiles
        percentiles = {
            'p1': np.percentile(simulated_values, 1),
            'p5': np.percentile(simulated_values, 5),
            'p25': np.percentile(simulated_values, 25),
            'p50': np.percentile(simulated_values, 50),
            'p75': np.percentile(simulated_values, 75),
            'p95': np.percentile(simulated_values, 95),
            'p99': np.percentile(simulated_values, 99)
        }
        
        # Probability of loss
        prob_loss = np.sum(simulated_values < baseline_value) / num_simulations
        
        result = {
            'test_type': 'monte_carlo',
            'num_simulations': num_simulations,
            'time_horizon_days': time_horizon_days,
            'baseline_value': baseline_value,
            'statistics': {
                'mean': mean_value,
                'median': median_value,
                'std_dev': std_value,
                'min': np.min(simulated_values),
                'max': np.max(simulated_values)
            },
            'var': var_results,
            'cvar': cvar_results,
            'percentiles': percentiles,
            'probability_of_loss': prob_loss,
            'expected_return': expected_return,
            'volatility': volatility,
            'simulated_paths': simulated_values.tolist()[:100],  # Return first 100 for visualization
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def run_custom_stress_test(
        self,
        test_id: str,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run custom stress test
        
        Args:
            test_id: Stress test ID
            portfolio_data: Portfolio data
            
        Returns:
            Test results
        """
        if test_id not in self.stress_tests:
            raise ValueError(f"Stress test {test_id} not found")
        
        test = self.stress_tests[test_id]
        params = test.parameters
        
        baseline_value = portfolio_data.get('total_value', 100000000)
        baseline_risk = portfolio_data.get('risk_score', 0.5)
        
        # Apply custom shocks
        total_impact = 0
        impact_details = {}
        
        for shock_type, shock_value in params.items():
            if shock_type == 'equity_shock':
                equity_exposure = portfolio_data.get('equity_exposure', 0.60)
                impact = baseline_value * equity_exposure * shock_value
                total_impact += impact
                impact_details['equity'] = impact
            
            elif shock_type == 'rate_shock':
                bond_exposure = portfolio_data.get('bond_exposure', 0.30)
                duration = portfolio_data.get('duration', 5.0)
                impact = -shock_value * duration * baseline_value * bond_exposure
                total_impact += impact
                impact_details['rates'] = impact
            
            elif shock_type == 'credit_shock':
                credit_exposure = portfolio_data.get('credit_exposure', 0.30)
                duration = portfolio_data.get('duration', 5.0)
                impact = -shock_value * duration * baseline_value * credit_exposure
                total_impact += impact
                impact_details['credit'] = impact
            
            elif shock_type == 'fx_shock':
                fx_exposure = portfolio_data.get('fx_exposure', 0.20)
                impact = baseline_value * fx_exposure * shock_value
                total_impact += impact
                impact_details['fx'] = impact
        
        stressed_value = baseline_value + total_impact
        risk_multiplier = params.get('risk_multiplier', 1.5)
        stressed_risk = min(1.0, baseline_risk * risk_multiplier)
        
        result = {
            'test_type': 'custom',
            'test_id': test_id,
            'test_name': test.name,
            'baseline': {
                'portfolio_value': baseline_value,
                'risk_score': baseline_risk
            },
            'stressed': {
                'portfolio_value': stressed_value,
                'risk_score': stressed_risk
            },
            'impact': {
                'total_loss': total_impact,
                'loss_percentage': (total_impact / baseline_value) * 100,
                'details': impact_details
            },
            'parameters': params,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def run_reverse_stress_test(
        self,
        portfolio_data: Dict[str, Any],
        target_loss_pct: float = 0.25
    ) -> Dict[str, Any]:
        """
        Run reverse stress test to find scenarios that cause target loss
        
        Args:
            portfolio_data: Portfolio data
            target_loss_pct: Target loss percentage (e.g., 0.25 for 25% loss)
            
        Returns:
            Reverse stress test results
        """
        logger.info(f"Running reverse stress test for {target_loss_pct*100}% loss")
        
        baseline_value = portfolio_data.get('total_value', 100000000)
        target_loss = baseline_value * target_loss_pct
        
        # Calculate required shocks
        equity_exposure = portfolio_data.get('equity_exposure', 0.60)
        bond_exposure = portfolio_data.get('bond_exposure', 0.30)
        duration = portfolio_data.get('duration', 5.0)
        
        # Scenario 1: Pure equity shock
        equity_shock_required = -target_loss_pct / equity_exposure if equity_exposure > 0 else 0
        
        # Scenario 2: Pure rate shock
        rate_shock_required = target_loss_pct / (duration * bond_exposure) if bond_exposure > 0 else 0
        
        # Scenario 3: Combined shock (50/50)
        combined_equity_shock = equity_shock_required * 0.5
        combined_rate_shock = rate_shock_required * 0.5
        
        result = {
            'test_type': 'reverse_stress',
            'target_loss': target_loss,
            'target_loss_percentage': target_loss_pct * 100,
            'baseline_value': baseline_value,
            'scenarios': {
                'pure_equity_shock': {
                    'equity_shock_pct': equity_shock_required * 100,
                    'description': f'{abs(equity_shock_required)*100:.1f}% equity market decline'
                },
                'pure_rate_shock': {
                    'rate_shock_bps': rate_shock_required * 10000,
                    'description': f'{rate_shock_required*10000:.0f} bps rate increase'
                },
                'combined_shock': {
                    'equity_shock_pct': combined_equity_shock * 100,
                    'rate_shock_bps': combined_rate_shock * 10000,
                    'description': f'{abs(combined_equity_shock)*100:.1f}% equity decline + {combined_rate_shock*10000:.0f} bps rate increase'
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def generate_stress_test_report(
        self,
        test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive stress test report
        
        Args:
            test_results: List of test results
            
        Returns:
            Stress test report
        """
        if not test_results:
            return {'error': 'No test results provided'}
        
        # Aggregate results
        worst_case = min(test_results, key=lambda x: x['stressed']['portfolio_value'])
        best_case = max(test_results, key=lambda x: x['stressed']['portfolio_value'])
        
        avg_loss = np.mean([r['impact']['total_loss'] for r in test_results])
        max_loss = min([r['impact']['total_loss'] for r in test_results])
        
        report = {
            'report_type': 'stress_test_summary',
            'num_tests': len(test_results),
            'summary': {
                'worst_case_scenario': worst_case.get('scenario', worst_case.get('test_name', 'Unknown')),
                'worst_case_loss': worst_case['impact']['total_loss'],
                'worst_case_loss_pct': worst_case['impact']['loss_percentage'],
                'best_case_scenario': best_case.get('scenario', best_case.get('test_name', 'Unknown')),
                'best_case_loss': best_case['impact']['total_loss'],
                'average_loss': avg_loss,
                'maximum_loss': max_loss
            },
            'all_results': test_results,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report


# Global stress testing service instance
_stress_testing_service = None


def get_stress_testing_service() -> StressTestingService:
    """Get or create global stress testing service instance"""
    global _stress_testing_service
    if _stress_testing_service is None:
        _stress_testing_service = StressTestingService()
    return _stress_testing_service


# Made with Bob