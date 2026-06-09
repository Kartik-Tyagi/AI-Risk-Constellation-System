"""
Transaction Data Generator for AI Risk Constellation System
Generates synthetic financial transactions between portfolios and counterparties.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path


class TransactionGenerator:
    """Generate synthetic transaction data for testing and demonstration."""
    
    def __init__(self, num_portfolios=50, num_counterparties=200, 
                 start_date='2022-01-01', end_date='2024-12-31', seed=42):
        """
        Initialize the transaction generator.
        
        Args:
            num_portfolios: Number of portfolios
            num_counterparties: Number of counterparties
            start_date: Start date for transactions
            end_date: End date for transactions
            seed: Random seed for reproducibility
        """
        self.num_portfolios = num_portfolios
        self.num_counterparties = num_counterparties
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.seed = seed
        np.random.seed(seed)
        
        # Generate IDs
        self.portfolio_ids = [f"PF{str(i).zfill(4)}" for i in range(num_portfolios)]
        self.counterparty_ids = [f"CP{str(i).zfill(4)}" for i in range(num_counterparties)]
        
        # Transaction types
        self.transaction_types = ['BUY', 'SELL', 'SWAP', 'DERIVATIVE', 'LOAN', 'REPO']
        self.asset_classes = ['EQUITY', 'FIXED_INCOME', 'COMMODITY', 'FX', 'DERIVATIVE', 'CRYPTO']
        
    def generate_transactions(self, num_transactions=10000):
        """
        Generate synthetic transactions.
        
        Args:
            num_transactions: Number of transactions to generate
            
        Returns:
            DataFrame with transaction data
        """
        transactions = []
        
        # Generate date range
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='h')
        
        for i in range(num_transactions):
            # Random date and time
            transaction_date = date_range[np.random.randint(len(date_range))]
            
            # Random portfolio and counterparty
            portfolio_id = np.random.choice(self.portfolio_ids)
            counterparty_id = np.random.choice(self.counterparty_ids)
            
            # Transaction details
            transaction_type = np.random.choice(self.transaction_types)
            asset_class = np.random.choice(self.asset_classes)
            
            # Amount (log-normal distribution)
            amount = np.random.lognormal(12, 2)  # Mean ~$150k, varies widely
            
            # Quantity
            quantity = np.random.randint(100, 10000)
            
            # Price per unit
            price = amount / quantity
            
            # Risk metrics
            var_95 = amount * np.random.uniform(0.01, 0.05)  # Value at Risk
            expected_shortfall = var_95 * np.random.uniform(1.2, 1.5)
            
            # Settlement date (T+2 for most)
            settlement_days = 2 if asset_class in ['EQUITY', 'FIXED_INCOME'] else np.random.randint(0, 5)
            settlement_date = transaction_date + timedelta(days=settlement_days)
            
            # Status
            if transaction_date < datetime.now():
                status = np.random.choice(['SETTLED', 'PENDING', 'FAILED'], p=[0.95, 0.04, 0.01])
            else:
                status = 'PENDING'
            
            transactions.append({
                'transaction_id': f"TXN{str(i).zfill(8)}",
                'transaction_date': transaction_date,
                'settlement_date': settlement_date,
                'portfolio_id': portfolio_id,
                'counterparty_id': counterparty_id,
                'transaction_type': transaction_type,
                'asset_class': asset_class,
                'quantity': quantity,
                'price': price,
                'amount': amount,
                'currency': 'USD',
                'var_95': var_95,
                'expected_shortfall': expected_shortfall,
                'status': status,
                'risk_score': np.random.uniform(0, 100)
            })
        
        return pd.DataFrame(transactions)
    
    def generate_transaction_network(self, transactions_df):
        """
        Generate network statistics from transactions.
        
        Args:
            transactions_df: DataFrame with transaction data
            
        Returns:
            Dictionary with network statistics
        """
        # Calculate exposure between portfolios and counterparties
        exposure = transactions_df.groupby(['portfolio_id', 'counterparty_id']).agg({
            'amount': 'sum',
            'transaction_id': 'count'
        }).reset_index()
        exposure.columns = ['portfolio_id', 'counterparty_id', 'total_exposure', 'num_transactions']
        
        # Calculate portfolio statistics
        portfolio_stats = transactions_df.groupby('portfolio_id').agg({
            'amount': ['sum', 'mean', 'std'],
            'var_95': 'sum',
            'expected_shortfall': 'sum',
            'counterparty_id': 'nunique',
            'transaction_id': 'count'
        }).reset_index()
        
        portfolio_stats.columns = [
            'portfolio_id', 'total_amount', 'avg_transaction', 'std_transaction',
            'total_var', 'total_es', 'num_counterparties', 'num_transactions'
        ]
        
        # Calculate counterparty statistics
        counterparty_stats = transactions_df.groupby('counterparty_id').agg({
            'amount': ['sum', 'mean', 'std'],
            'portfolio_id': 'nunique',
            'transaction_id': 'count'
        }).reset_index()
        
        counterparty_stats.columns = [
            'counterparty_id', 'total_amount', 'avg_transaction', 'std_transaction',
            'num_portfolios', 'num_transactions'
        ]
        
        return {
            'exposure': exposure,
            'portfolio_stats': portfolio_stats,
            'counterparty_stats': counterparty_stats
        }
    
    def generate_all(self, num_transactions=10000, output_dir='data/synthetic'):
        """
        Generate all transaction data and save to files.
        
        Args:
            num_transactions: Number of transactions to generate
            output_dir: Directory to save generated data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating {num_transactions} transactions...")
        
        # Generate transactions
        transactions_df = self.generate_transactions(num_transactions)
        
        # Generate network statistics
        print("Calculating network statistics...")
        network_stats = self.generate_transaction_network(transactions_df)
        
        # Save to CSV
        print("Saving data to CSV files...")
        transactions_df.to_csv(output_path / 'transactions.csv', index=False)
        network_stats['exposure'].to_csv(output_path / 'exposure_network.csv', index=False)
        network_stats['portfolio_stats'].to_csv(output_path / 'portfolio_transaction_stats.csv', index=False)
        network_stats['counterparty_stats'].to_csv(output_path / 'counterparty_transaction_stats.csv', index=False)
        
        print(f"✅ Transaction data generation complete!")
        print(f"   - {len(transactions_df)} transactions")
        print(f"   - {len(network_stats['exposure'])} portfolio-counterparty pairs")
        print(f"   - {self.num_portfolios} portfolios")
        print(f"   - {self.num_counterparties} counterparties")
        print(f"   - Date range: {self.start_date.date()} to {self.end_date.date()}")
        
        return transactions_df, network_stats


if __name__ == '__main__':
    # Generate transaction data
    generator = TransactionGenerator(
        num_portfolios=50,
        num_counterparties=200,
        start_date='2022-01-01',
        end_date='2024-12-31',
        seed=42
    )
    
    generator.generate_all(num_transactions=10000)

# Made with Bob
