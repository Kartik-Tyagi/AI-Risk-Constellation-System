import React, { useState, useEffect } from 'react';
import './ScenarioAnalysis.css';

/**
 * ScenarioAnalysis Component
 * UI for scenario analysis and stress testing
 */
const ScenarioAnalysis = () => {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [scenarioResults, setScenarioResults] = useState(null);
  const [stressTestResults, setStressTestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Scenario builder state
  const [scenarioName, setScenarioName] = useState('');
  const [scenarioType, setScenarioType] = useState('custom');
  const [scenarioDescription, setScenarioDescription] = useState('');
  const [scenarioParameters, setScenarioParameters] = useState({});
  
  // Portfolio data (would come from context/props in production)
  const [portfolioData, setPortfolioData] = useState({
    total_value: 100000000,
    equity_exposure: 0.60,
    bond_exposure: 0.30,
    credit_exposure: 0.25,
    fx_exposure: 0.20,
    commodity_exposure: 0.10,
    illiquid_assets: 0.20,
    duration: 5.0,
    risk_score: 0.5,
    expected_return: 0.08,
    volatility: 0.15
  });
  
  // Monte Carlo parameters
  const [monteCarloParams, setMonteCarloParams] = useState({
    num_simulations: 10000,
    time_horizon_days: 252,
    confidence_levels: [0.95, 0.99]
  });

  // Load scenarios on mount
  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/scenarios/list?include_predefined=true');
      const data = await response.json();
      setScenarios(data.scenarios || []);
      setError(null);
    } catch (err) {
      setError('Failed to load scenarios: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const createScenario = async () => {
    if (!scenarioName || !scenarioDescription) {
      setError('Please provide scenario name and description');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/scenarios/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scenarioName,
          scenario_type: scenarioType,
          description: scenarioDescription,
          parameters: scenarioParameters,
          severity: 'medium'
        })
      });

      if (!response.ok) throw new Error('Failed to create scenario');

      const data = await response.json();
      setError(null);
      alert(`Scenario created: ${data.scenario_id}`);
      loadScenarios();
      
      // Reset form
      setScenarioName('');
      setScenarioDescription('');
      setScenarioParameters({});
    } catch (err) {
      setError('Failed to create scenario: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const applyScenario = async (scenarioId) => {
    try {
      setLoading(true);
      const response = await fetch('/api/scenarios/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenarioId,
          portfolio_data: portfolioData
        })
      });

      if (!response.ok) throw new Error('Failed to apply scenario');

      const data = await response.json();
      setScenarioResults(data);
      setError(null);
    } catch (err) {
      setError('Failed to apply scenario: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runHistoricalStressTest = async (scenarioKey) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/scenarios/stress-test/historical/${scenarioKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(portfolioData)
      });

      if (!response.ok) throw new Error('Failed to run stress test');

      const data = await response.json();
      setStressTestResults(data);
      setError(null);
    } catch (err) {
      setError('Failed to run stress test: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runMonteCarloSimulation = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/scenarios/stress-test/monte-carlo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_data: portfolioData,
          ...monteCarloParams
        })
      });

      if (!response.ok) throw new Error('Failed to run Monte Carlo simulation');

      const data = await response.json();
      setStressTestResults(data);
      setError(null);
    } catch (err) {
      setError('Failed to run Monte Carlo simulation: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateParameter = (key, value) => {
    setScenarioParameters({
      ...scenarioParameters,
      [key]: parseFloat(value) || 0
    });
  };

  const renderScenarioBuilder = () => (
    <div className="scenario-builder">
      <h3>Create Custom Scenario</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-section">
        <label>Scenario Name:</label>
        <input
          type="text"
          value={scenarioName}
          onChange={(e) => setScenarioName(e.target.value)}
          placeholder="e.g., Custom Market Shock"
          disabled={loading}
        />
      </div>

      <div className="form-section">
        <label>Scenario Type:</label>
        <select
          value={scenarioType}
          onChange={(e) => setScenarioType(e.target.value)}
          disabled={loading}
        >
          <option value="custom">Custom</option>
          <option value="market_crash">Market Crash</option>
          <option value="interest_rate_shock">Interest Rate Shock</option>
          <option value="credit_spread_widening">Credit Spread Widening</option>
          <option value="counterparty_default">Counterparty Default</option>
          <option value="liquidity_crisis">Liquidity Crisis</option>
          <option value="currency_shock">Currency Shock</option>
          <option value="commodity_shock">Commodity Shock</option>
        </select>
      </div>

      <div className="form-section">
        <label>Description:</label>
        <textarea
          value={scenarioDescription}
          onChange={(e) => setScenarioDescription(e.target.value)}
          placeholder="Describe the scenario..."
          rows="3"
          disabled={loading}
        />
      </div>

      <div className="parameters-section">
        <h4>Scenario Parameters</h4>
        <div className="parameters-grid">
          <div className="parameter-input">
            <label>Equity Shock (%):</label>
            <input
              type="number"
              step="0.01"
              value={scenarioParameters.equity_shock || ''}
              onChange={(e) => updateParameter('equity_shock', e.target.value)}
              placeholder="e.g., -0.30 for -30%"
              disabled={loading}
            />
          </div>

          <div className="parameter-input">
            <label>Rate Shock (bps):</label>
            <input
              type="number"
              step="0.0001"
              value={scenarioParameters.rate_shock || ''}
              onChange={(e) => updateParameter('rate_shock', e.target.value)}
              placeholder="e.g., 0.02 for 200bps"
              disabled={loading}
            />
          </div>

          <div className="parameter-input">
            <label>Credit Spread (bps):</label>
            <input
              type="number"
              step="0.0001"
              value={scenarioParameters.credit_shock || ''}
              onChange={(e) => updateParameter('credit_shock', e.target.value)}
              placeholder="e.g., 0.03 for 300bps"
              disabled={loading}
            />
          </div>

          <div className="parameter-input">
            <label>FX Shock (%):</label>
            <input
              type="number"
              step="0.01"
              value={scenarioParameters.fx_shock || ''}
              onChange={(e) => updateParameter('fx_shock', e.target.value)}
              placeholder="e.g., -0.20 for -20%"
              disabled={loading}
            />
          </div>

          <div className="parameter-input">
            <label>Risk Multiplier:</label>
            <input
              type="number"
              step="0.1"
              value={scenarioParameters.risk_multiplier || ''}
              onChange={(e) => updateParameter('risk_multiplier', e.target.value)}
              placeholder="e.g., 1.5"
              disabled={loading}
            />
          </div>
        </div>
      </div>

      <button
        className="btn-primary"
        onClick={createScenario}
        disabled={loading}
      >
        {loading ? 'Creating...' : 'Create Scenario'}
      </button>
    </div>
  );

  const renderScenarioList = () => (
    <div className="scenario-list">
      <h3>Available Scenarios</h3>
      
      {scenarios.length === 0 ? (
        <p>No scenarios available. Create one using the builder.</p>
      ) : (
        <div className="scenarios-grid">
          {scenarios.map(scenario => (
            <div key={scenario.scenario_id} className="scenario-card">
              <div className="scenario-header">
                <h4>{scenario.name}</h4>
                <span className={`severity-badge severity-${scenario.severity}`}>
                  {scenario.severity}
                </span>
              </div>
              <p className="scenario-description">{scenario.description}</p>
              <div className="scenario-meta">
                <span className="scenario-type">{scenario.type}</span>
                {scenario.is_predefined && (
                  <span className="predefined-badge">Predefined</span>
                )}
              </div>
              <button
                className="btn-small"
                onClick={() => applyScenario(scenario.scenario_id)}
                disabled={loading}
              >
                Apply Scenario
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderResults = () => {
    if (!scenarioResults) return null;

    const impact = scenarioResults.impact;
    const isLoss = impact.value_change < 0;

    return (
      <div className="results-panel">
        <h3>Scenario Results: {scenarioResults.scenario_name}</h3>
        
        <div className="results-summary">
          <div className="result-card">
            <h4>Baseline Portfolio Value</h4>
            <p className="value">${(scenarioResults.baseline.portfolio_value / 1000000).toFixed(2)}M</p>
          </div>

          <div className="result-card">
            <h4>Stressed Portfolio Value</h4>
            <p className="value">${(scenarioResults.stressed.portfolio_value / 1000000).toFixed(2)}M</p>
          </div>

          <div className={`result-card ${isLoss ? 'negative' : 'positive'}`}>
            <h4>Value Change</h4>
            <p className="value">
              {isLoss ? '-' : '+'}${Math.abs(impact.value_change / 1000000).toFixed(2)}M
              <span className="percentage">({impact.value_change_pct.toFixed(2)}%)</span>
            </p>
          </div>

          <div className="result-card">
            <h4>Risk Score Change</h4>
            <p className="value">
              {scenarioResults.baseline.risk_score.toFixed(3)} → {scenarioResults.stressed.risk_score.toFixed(3)}
              <span className="percentage">({impact.risk_change_pct.toFixed(1)}%)</span>
            </p>
          </div>
        </div>

        {scenarioResults.details && (
          <div className="results-details">
            <h4>Impact Breakdown</h4>
            <table className="details-table">
              <tbody>
                {Object.entries(scenarioResults.details).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key.replace(/_/g, ' ').toUpperCase()}</td>
                    <td>{typeof value === 'number' ? value.toFixed(4) : value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderStressTestTab = () => (
    <div className="stress-test-tab">
      <h3>Stress Testing</h3>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="stress-test-options">
        <div className="test-option">
          <h4>Historical Scenarios</h4>
          <p>Test against historical market events</p>
          <div className="historical-scenarios">
            <button onClick={() => runHistoricalStressTest('financial_crisis_2008')} disabled={loading}>
              2008 Financial Crisis
            </button>
            <button onClick={() => runHistoricalStressTest('covid_crash_2020')} disabled={loading}>
              COVID-19 Crash 2020
            </button>
            <button onClick={() => runHistoricalStressTest('dot_com_crash_2000')} disabled={loading}>
              Dot-com Crash 2000
            </button>
            <button onClick={() => runHistoricalStressTest('black_monday_1987')} disabled={loading}>
              Black Monday 1987
            </button>
          </div>
        </div>

        <div className="test-option">
          <h4>Monte Carlo Simulation</h4>
          <p>Run probabilistic simulation</p>
          <div className="monte-carlo-params">
            <div className="param-input">
              <label>Simulations:</label>
              <input
                type="number"
                value={monteCarloParams.num_simulations}
                onChange={(e) => setMonteCarloParams({
                  ...monteCarloParams,
                  num_simulations: parseInt(e.target.value) || 10000
                })}
                disabled={loading}
              />
            </div>
            <div className="param-input">
              <label>Time Horizon (days):</label>
              <input
                type="number"
                value={monteCarloParams.time_horizon_days}
                onChange={(e) => setMonteCarloParams({
                  ...monteCarloParams,
                  time_horizon_days: parseInt(e.target.value) || 252
                })}
                disabled={loading}
              />
            </div>
          </div>
          <button
            className="btn-primary"
            onClick={runMonteCarloSimulation}
            disabled={loading}
          >
            {loading ? 'Running...' : 'Run Monte Carlo'}
          </button>
        </div>
      </div>

      {stressTestResults && renderStressTestResults()}
    </div>
  );

  const renderStressTestResults = () => {
    if (!stressTestResults) return null;

    if (stressTestResults.test_type === 'monte_carlo') {
      return (
        <div className="monte-carlo-results">
          <h4>Monte Carlo Results</h4>
          <div className="results-grid">
            <div className="result-card">
              <h5>Mean Value</h5>
              <p>${(stressTestResults.statistics.mean / 1000000).toFixed(2)}M</p>
            </div>
            <div className="result-card">
              <h5>VaR 95%</h5>
              <p>${(stressTestResults.var.var_95.loss / 1000000).toFixed(2)}M</p>
              <span>({stressTestResults.var.var_95.loss_percentage.toFixed(2)}%)</span>
            </div>
            <div className="result-card">
              <h5>VaR 99%</h5>
              <p>${(stressTestResults.var.var_99.loss / 1000000).toFixed(2)}M</p>
              <span>({stressTestResults.var.var_99.loss_percentage.toFixed(2)}%)</span>
            </div>
            <div className="result-card">
              <h5>Probability of Loss</h5>
              <p>{(stressTestResults.probability_of_loss * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="stress-test-results">
        <h4>Stress Test Results: {stressTestResults.scenario}</h4>
        <div className="results-grid">
          <div className="result-card">
            <h5>Total Loss</h5>
            <p className="negative">${Math.abs(stressTestResults.impact.total_loss / 1000000).toFixed(2)}M</p>
            <span>({stressTestResults.impact.loss_percentage.toFixed(2)}%)</span>
          </div>
          <div className="result-card">
            <h5>Stressed Value</h5>
            <p>${(stressTestResults.stressed.portfolio_value / 1000000).toFixed(2)}M</p>
          </div>
          <div className="result-card">
            <h5>Risk Score</h5>
            <p>{stressTestResults.stressed.risk_score.toFixed(3)}</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="scenario-analysis">
      <div className="scenario-header">
        <h2>Scenario Analysis & Stress Testing</h2>
        <p>Test portfolio resilience under various market conditions</p>
      </div>

      <div className="scenario-tabs">
        <button
          className={`tab-button ${activeTab === 'scenarios' ? 'active' : ''}`}
          onClick={() => setActiveTab('scenarios')}
        >
          Scenarios
        </button>
        <button
          className={`tab-button ${activeTab === 'builder' ? 'active' : ''}`}
          onClick={() => setActiveTab('builder')}
        >
          Scenario Builder
        </button>
        <button
          className={`tab-button ${activeTab === 'stress-test' ? 'active' : ''}`}
          onClick={() => setActiveTab('stress-test')}
        >
          Stress Testing
        </button>
        <button
          className={`tab-button ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          Results
        </button>
      </div>

      <div className="scenario-content">
        {activeTab === 'scenarios' && renderScenarioList()}
        {activeTab === 'builder' && renderScenarioBuilder()}
        {activeTab === 'stress-test' && renderStressTestTab()}
        {activeTab === 'results' && renderResults()}
      </div>
    </div>
  );
};

export default ScenarioAnalysis;

// Made with Bob