"""
Scenario Analysis API Routes
Endpoints for scenario analysis and stress testing
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel, Field
except ImportError:
    # Placeholder for when FastAPI is not installed
    class APIRouter:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail): pass
    
    def Query(**kwargs): return None
    
    class BaseModel: pass
    class Field:
        def __init__(self, *args, **kwargs): pass

from backend.services.scenario_engine import get_scenario_engine, ScenarioType
from backend.services.stress_testing import get_stress_testing_service

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


# Request/Response Models
class ScenarioCreateRequest(BaseModel):
    """Request to create a scenario"""
    name: str
    scenario_type: str
    description: str
    parameters: Dict[str, Any]
    severity: str = "medium"


class ScenarioApplyRequest(BaseModel):
    """Request to apply a scenario"""
    scenario_id: str
    portfolio_data: Dict[str, Any]
    entity_data: Optional[List[Dict[str, Any]]] = None


class ScenarioCompareRequest(BaseModel):
    """Request to compare scenarios"""
    scenario_ids: List[str]
    portfolio_data: Dict[str, Any]


class StressTestRequest(BaseModel):
    """Request to run stress test"""
    test_type: str  # historical, monte_carlo, custom, reverse
    portfolio_data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation"""
    portfolio_data: Dict[str, Any]
    num_simulations: int = 10000
    time_horizon_days: int = 252
    confidence_levels: List[float] = [0.95, 0.99]


# Scenario Endpoints
@router.get("/list")
async def list_scenarios(include_predefined: bool = Query(default=True)):
    """List all available scenarios"""
    try:
        engine = get_scenario_engine()
        scenarios = engine.list_scenarios(include_predefined=include_predefined)
        
        return {
            'scenarios': scenarios,
            'total': len(scenarios)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get scenario details"""
    try:
        engine = get_scenario_engine()
        scenario = engine.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        
        return {
            'scenario_id': scenario.scenario_id,
            'name': scenario.name,
            'type': scenario.scenario_type.value,
            'description': scenario.description,
            'parameters': scenario.parameters,
            'severity': scenario.severity,
            'created_at': scenario.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scenario: {str(e)}")


@router.post("/create")
async def create_scenario(request: ScenarioCreateRequest):
    """Create a new scenario"""
    try:
        engine = get_scenario_engine()
        
        scenario = engine.create_scenario(
            name=request.name,
            scenario_type=request.scenario_type,
            description=request.description,
            parameters=request.parameters,
            severity=request.severity
        )
        
        return {
            'scenario_id': scenario.scenario_id,
            'name': scenario.name,
            'type': scenario.scenario_type.value,
            'description': scenario.description,
            'severity': scenario.severity,
            'created_at': scenario.created_at,
            'message': 'Scenario created successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")


@router.post("/apply")
async def apply_scenario(request: ScenarioApplyRequest):
    """Apply a scenario to portfolio"""
    try:
        engine = get_scenario_engine()
        
        result = engine.apply_scenario(
            scenario_id=request.scenario_id,
            portfolio_data=request.portfolio_data,
            entity_data=request.entity_data
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply scenario: {str(e)}")


@router.post("/compare")
async def compare_scenarios(request: ScenarioCompareRequest):
    """Compare multiple scenarios"""
    try:
        engine = get_scenario_engine()
        
        comparison = engine.compare_scenarios(
            scenario_ids=request.scenario_ids,
            portfolio_data=request.portfolio_data
        )
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare scenarios: {str(e)}")


# Stress Testing Endpoints
@router.get("/stress-test/historical")
async def list_historical_scenarios():
    """List available historical stress scenarios"""
    try:
        service = get_stress_testing_service()
        scenarios = service.historical_scenarios
        
        return {
            'scenarios': [
                {
                    'key': key,
                    'name': data['name'],
                    'date': data['date'],
                    'description': f"Historical scenario from {data['date']}"
                }
                for key, data in scenarios.items()
            ],
            'total': len(scenarios)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list historical scenarios: {str(e)}")


@router.post("/stress-test/historical/{scenario_key}")
async def run_historical_stress_test(
    scenario_key: str,
    portfolio_data: Dict[str, Any]
):
    """Run historical stress test"""
    try:
        service = get_stress_testing_service()
        
        result = service.run_historical_stress_test(
            scenario_key=scenario_key,
            portfolio_data=portfolio_data
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run historical stress test: {str(e)}")


@router.post("/stress-test/monte-carlo")
async def run_monte_carlo_simulation(request: MonteCarloRequest):
    """Run Monte Carlo simulation"""
    try:
        service = get_stress_testing_service()
        
        result = service.run_monte_carlo_simulation(
            portfolio_data=request.portfolio_data,
            num_simulations=request.num_simulations,
            time_horizon_days=request.time_horizon_days,
            confidence_levels=request.confidence_levels
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run Monte Carlo simulation: {str(e)}")


@router.post("/stress-test/custom")
async def create_custom_stress_test(
    name: str,
    description: str,
    parameters: Dict[str, Any]
):
    """Create a custom stress test"""
    try:
        service = get_stress_testing_service()
        
        test = service.create_stress_test(
            name=name,
            test_type='custom',
            description=description,
            parameters=parameters
        )
        
        return {
            'test_id': test.test_id,
            'name': test.name,
            'test_type': test.test_type,
            'description': test.description,
            'created_at': test.created_at,
            'message': 'Custom stress test created successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create custom stress test: {str(e)}")


@router.post("/stress-test/custom/{test_id}/run")
async def run_custom_stress_test(
    test_id: str,
    portfolio_data: Dict[str, Any]
):
    """Run a custom stress test"""
    try:
        service = get_stress_testing_service()
        
        result = service.run_custom_stress_test(
            test_id=test_id,
            portfolio_data=portfolio_data
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run custom stress test: {str(e)}")


@router.post("/stress-test/reverse")
async def run_reverse_stress_test(
    portfolio_data: Dict[str, Any],
    target_loss_pct: float = Query(default=0.25, ge=0.01, le=1.0)
):
    """Run reverse stress test"""
    try:
        service = get_stress_testing_service()
        
        result = service.run_reverse_stress_test(
            portfolio_data=portfolio_data,
            target_loss_pct=target_loss_pct
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run reverse stress test: {str(e)}")


@router.post("/stress-test/report")
async def generate_stress_test_report(test_results: List[Dict[str, Any]]):
    """Generate comprehensive stress test report"""
    try:
        service = get_stress_testing_service()
        
        report = service.generate_stress_test_report(test_results=test_results)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate stress test report: {str(e)}")


@router.post("/stress-test/batch")
async def run_batch_stress_tests(
    portfolio_data: Dict[str, Any],
    test_types: List[str] = Query(default=["market_crash_2008", "financial_crisis_2008", "covid_crash_2020"])
):
    """Run multiple stress tests in batch"""
    try:
        service = get_stress_testing_service()
        results = []
        
        for test_type in test_types:
            try:
                if test_type in service.historical_scenarios:
                    result = service.run_historical_stress_test(
                        scenario_key=test_type,
                        portfolio_data=portfolio_data
                    )
                    results.append(result)
            except Exception as e:
                # Log error but continue with other tests
                results.append({
                    'test_type': test_type,
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Generate summary report
        report = service.generate_stress_test_report(
            test_results=[r for r in results if 'error' not in r]
        )
        
        return {
            'individual_results': results,
            'summary_report': report,
            'total_tests': len(test_types),
            'successful_tests': len([r for r in results if 'error' not in r]),
            'failed_tests': len([r for r in results if 'error' in r])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run batch stress tests: {str(e)}")


# Made with Bob