"""
Portfolio Data Generator for AI Risk Constellation System
Generates synthetic portfolio holdings and allocations.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path


class PortfolioGenerator:
    """Generate synthetic portfolio data for testing and demonstration."""
    
    def __init__(self, num_portfolios=50, tickers=None, seed=42):
        """
        Initialize the portfolio generator.
        
        Args:
            num_portfolios: Number of portfolios to generate
            tickers: List of available tickers (if None, will generate)
            seed: Random seed for reproducibility
        """
        self.num_portfolios = num_portfolios
        self.seed = seed
        np.random.seed(seed)
        
        # Generate or use provided tickers
        if tickers is None:
            sectors = ['TECH', 'FIN', 'HLTH', 'ENRG', 'CONS', 'IND', 'MAT', 'UTIL', 'REAL', 'COMM']
            self.tickers = [f"{sectors[i % len(sectors)]}{str(i).zfill(3)}" for i in range(100)]
        else:
            self.tickers = tickers
        
        # Portfolio types
        self.portfolio_types = ['AGGRESSIVE', 'MODERATE', 'CONSERVATIVE', 'BALANCED', 'INCOME']
        self.strategies = ['GROWTH', 'VALUE', 'MOMENTUM', 'DIVIDEND', 'INDEX', 'HEDGE']
        
    def generate_portfolio_metadata(self):
        """
        Generate portfolio metadata.
        
        Returns:
            List of portfolio metadata dictionaries
        """
        portfolios = []
        
        for i in range(self.num_portfolios):
            portfolio_id = f"PF{str(i).zfill(4)}"
            portfolio_type = np.random.choice(self.portfolio_types)
            strategy = np.random.choice(self.strategies)
            
            # Portfolio characteristics based on type
            if portfolio_type == 'AGGRESSIVE':
                target_return = np.random.uniform(0.12, 0.20)
                risk_tolerance = np.random.uniform(0.15, 0.25)
                max_concentration = 0.15
            elif portfolio_type == 'MODERATE':
                target_return = np.random.uniform(0.08, 0.12)
                risk_tolerance = np.random.uniform(0.10, 0.15)
                max_concentration = 0.10
            elif portfolio_type == 'CONSERVATIVE':
                target_return = np.random.uniform(0.04, 0.08)
                risk_tolerance = np.random.uniform(0.05, 0.10)
                max_concentration = 0.08
            elif portfolio_type == 'BALANCED':
                target_return = np.random.uniform(0.07, 0.11)
                risk_tolerance = np.random.uniform(0.08, 0.13)
                max_concentration = 0.12
            else:  # INCOME
                target_return = np.random.uniform(0.05, 0.09)
                risk_tolerance = np.random.uniform(0.06, 0.11)
                max_concentration = 0.10
            
            # Total portfolio value
            total_value = np.random.lognormal(18, 1.5)  # Mean ~$100M, varies widely
            
            portfolios.append({
                'portfolio_id': portfolio_id,
                'portfolio_name': f"Portfolio {i+1}",
                'portfolio_type': portfolio_type,
                'strategy': strategy,
                'total_value': total_value,
                'target_return': target_return,
                'risk_tolerance': risk_tolerance,
                'max_concentration': max_concentration,
                'inception_date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=np.random.randint(0, 1000)),
                'manager_id': f"MGR{np.random.randint(1, 20):03d}",
                'benchmark': np.random.choice(['SP500', 'NASDAQ', 'RUSSELL2000', 'MSCI_WORLD'])
            })
        
        return portfolios
    
    def generate_holdings(self, portfolio_metadata):
        """
        Generate portfolio holdings.
        
        Args:
            portfolio_metadata: List of portfolio metadata
            
        Returns:
            DataFrame with holdings data
        """
        all_holdings = []
        
        for portfolio in portfolio_metadata:
            portfolio_id = portfolio['portfolio_id']
            total_value = portfolio['total_value']
            portfolio_type = portfolio['portfolio_type']
            
            # Number of holdings based on portfolio type
            if portfolio_type == 'AGGRESSIVE':
                num_holdings = np.random.randint(15, 30)
            elif portfolio_type == 'CONSERVATIVE':
                num_holdings = np.random.randint(30, 60)
            else:
                num_holdings = np.random.randint(20, 40)
            
            # Select random tickers
            selected_tickers = np.random.choice(self.tickers, size=num_holdings, replace=False)
            
            # Generate weights using Dirichlet distribution for realistic allocation
            alpha = np.ones(num_holdings) * 2  # Concentration parameter
            weights = np.random.dirichlet(alpha)
            
            # Ensure no position exceeds max concentration
            max_concentration = portfolio['max_concentration']
            weights = np.minimum(weights, max_concentration)
            weights = weights / weights.sum()  # Renormalize
            
            # Calculate position values
            position_values = weights * total_value
            
            # Generate holdings
            for ticker, weight, value in zip(selected_tickers, weights, position_values):
                # Estimate shares (assuming price around $100)
                estimated_price = np.random.uniform(50, 200)
                shares = int(value / estimated_price)
                
                # Risk metrics
                position_var = value * np.random.uniform(0.02, 0.08)
                position_beta = np.random.normal(1.0, 0.3)
                
                all_holdings.append({
                    'portfolio_id': portfolio_id,
                    'ticker': ticker,
                    'shares': shares,
                    'estimated_price': estimated_price,
                    'market_value': value,
                    'weight': weight,
                    'cost_basis': value * np.random.uniform(0.8, 1.2),
                    'unrealized_pnl': value * np.random.normal(0, 0.1),
                    'position_var_95': position_var,
                    'position_beta': position_beta,
                    'sector': ticker[:4],
                    'last_updated': pd.Timestamp.now()
                })
        
        return pd.DataFrame(all_holdings)
    
    def calculate_portfolio_metrics(self, holdings_df, portfolio_metadata):
        """
        Calculate portfolio-level risk metrics.
        
        Args:
            holdings_df: DataFrame with holdings
            portfolio_metadata: List of portfolio metadata
            
        Returns:
            DataFrame with portfolio metrics
        """
        metrics = []
        
        for portfolio in portfolio_metadata:
            portfolio_id = portfolio['portfolio_id']
            portfolio_holdings = holdings_df[holdings_df['portfolio_id'] == portfolio_id]
            
            if len(portfolio_holdings) == 0:
                continue
            
            # Calculate metrics
            total_value = portfolio_holdings['market_value'].sum()
            num_positions = len(portfolio_holdings)
            
            # Concentration metrics
            max_position = portfolio_holdings['weight'].max()
            top_5_concentration = portfolio_holdings.nlargest(5, 'weight')['weight'].sum()
            
            # Risk metrics
            portfolio_var = portfolio_holdings['position_var_95'].sum()
            portfolio_beta = (portfolio_holdings['position_beta'] * portfolio_holdings['weight']).sum()
            
            # Sector allocation
            sector_allocation = portfolio_holdings.groupby('sector')['weight'].sum().to_dict()
            
            # Performance metrics (simulated)
            ytd_return = np.random.normal(0.08, 0.15)
            sharpe_ratio = np.random.uniform(0.5, 2.0)
            max_drawdown = np.random.uniform(-0.05, -0.25)
            
            metrics.append({
                'portfolio_id': portfolio_id,
                'total_value': total_value,
                'num_positions': num_positions,
                'max_position_weight': max_position,
                'top_5_concentration': top_5_concentration,
                'portfolio_var_95': portfolio_var,
                'portfolio_beta': portfolio_beta,
                'ytd_return': ytd_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'sector_allocation': json.dumps(sector_allocation),
                'diversification_ratio': num_positions / (1 + top_5_concentration)
            })
        
        return pd.DataFrame(metrics)
    
    def generate_all(self, output_dir='data/synthetic'):
        """
        Generate all portfolio data and save to files.
        
        Args:
            output_dir: Directory to save generated data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating {self.num_portfolios} portfolios...")
        
        # Generate portfolio metadata
        portfolio_metadata = self.generate_portfolio_metadata()
        
        # Generate holdings
        print("Generating portfolio holdings...")
        holdings_df = self.generate_holdings(portfolio_metadata)
        
        # Calculate portfolio metrics
        print("Calculating portfolio metrics...")
        metrics_df = self.calculate_portfolio_metrics(holdings_df, portfolio_metadata)
        
        # Save to CSV and JSON
        print("Saving data to files...")
        holdings_df.to_csv(output_path / 'portfolio_holdings.csv', index=False)
        metrics_df.to_csv(output_path / 'portfolio_metrics.csv', index=False)
        
        with open(output_path / 'portfolio_metadata.json', 'w') as f:
            # Convert Timestamp to string for JSON serialization
            for p in portfolio_metadata:
                p['inception_date'] = str(p['inception_date'])
            json.dump(portfolio_metadata, f, indent=2)
        
        print(f"✅ Portfolio data generation complete!")
        print(f"   - {self.num_portfolios} portfolios")
        print(f"   - {len(holdings_df)} holdings")
        print(f"   - Total portfolio value: ${metrics_df['total_value'].sum()/1e9:.2f}B")
        
        return holdings_df, metrics_df, portfolio_metadata


if __name__ == '__main__':
    # Generate portfolio data
    generator = PortfolioGenerator(
        num_portfolios=50,
        seed=42
    )
    
    generator.generate_all()

# Made with Bob
