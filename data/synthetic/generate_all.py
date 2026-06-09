"""
Master script to generate all synthetic data for AI Risk Constellation System
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from data.synthetic.market_data_generator import MarketDataGenerator
from data.synthetic.transaction_generator import TransactionGenerator
from data.synthetic.portfolio_generator import PortfolioGenerator
from data.synthetic.counterparty_generator import CounterpartyGenerator


def generate_all_data(output_dir='data/synthetic', seed=42):
    """
    Generate all synthetic data for the system.
    
    Args:
        output_dir: Directory to save generated data
        seed: Random seed for reproducibility
    """
    print("=" * 80)
    print("AI RISK CONSTELLATION SYSTEM - SYNTHETIC DATA GENERATION")
    print("=" * 80)
    print()
    
    # Configuration
    config = {
        'num_tickers': 100,
        'num_portfolios': 50,
        'num_counterparties': 200,
        'num_transactions': 10000,
        'start_date': '2022-01-01',
        'end_date': '2024-12-31',
        'seed': seed
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # Step 1: Generate Market Data
    print("\n" + "=" * 80)
    print("STEP 1: GENERATING MARKET DATA")
    print("=" * 80)
    market_generator = MarketDataGenerator(
        num_tickers=config['num_tickers'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        seed=config['seed']
    )
    market_prices, market_conditions, ticker_metadata = market_generator.generate_all(output_dir)
    
    # Step 2: Generate Portfolio Data
    print("\n" + "=" * 80)
    print("STEP 2: GENERATING PORTFOLIO DATA")
    print("=" * 80)
    portfolio_generator = PortfolioGenerator(
        num_portfolios=config['num_portfolios'],
        tickers=market_generator.tickers,
        seed=config['seed']
    )
    holdings, portfolio_metrics, portfolio_metadata = portfolio_generator.generate_all(output_dir)
    
    # Step 3: Generate Counterparty Network
    print("\n" + "=" * 80)
    print("STEP 3: GENERATING COUNTERPARTY NETWORK")
    print("=" * 80)
    counterparty_generator = CounterpartyGenerator(
        num_counterparties=config['num_counterparties'],
        seed=config['seed']
    )
    cp_metadata, relationships, network_metrics, network_graph = counterparty_generator.generate_all(output_dir)
    
    # Step 4: Generate Transaction Data
    print("\n" + "=" * 80)
    print("STEP 4: GENERATING TRANSACTION DATA")
    print("=" * 80)
    transaction_generator = TransactionGenerator(
        num_portfolios=config['num_portfolios'],
        num_counterparties=config['num_counterparties'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        seed=config['seed']
    )
    transactions, transaction_network = transaction_generator.generate_all(
        num_transactions=config['num_transactions'],
        output_dir=output_dir
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("DATA GENERATION SUMMARY")
    print("=" * 80)
    print(f"✅ Market Data:")
    print(f"   - {len(market_prices)} price records")
    print(f"   - {config['num_tickers']} tickers")
    print(f"   - {len(market_conditions)} market condition records")
    print()
    print(f"✅ Portfolio Data:")
    print(f"   - {config['num_portfolios']} portfolios")
    print(f"   - {len(holdings)} holdings")
    print(f"   - Total AUM: ${portfolio_metrics['total_value'].sum()/1e9:.2f}B")
    print()
    print(f"✅ Counterparty Network:")
    print(f"   - {config['num_counterparties']} counterparties")
    print(f"   - {len(relationships)} relationships")
    print(f"   - Network density: {len(relationships) * 2 / (config['num_counterparties'] * (config['num_counterparties'] - 1)):.3f}")
    print()
    print(f"✅ Transaction Data:")
    print(f"   - {config['num_transactions']} transactions")
    print(f"   - {len(transaction_network['exposure'])} portfolio-counterparty pairs")
    print()
    print("=" * 80)
    print("ALL DATA GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("Generated files in", output_dir + ":")
    print("  - market_prices.csv")
    print("  - market_conditions.csv")
    print("  - ticker_metadata.json")
    print("  - portfolio_holdings.csv")
    print("  - portfolio_metrics.csv")
    print("  - portfolio_metadata.json")
    print("  - counterparty_relationships.csv")
    print("  - counterparty_network_metrics.csv")
    print("  - counterparty_metadata.json")
    print("  - counterparty_network.gexf")
    print("  - transactions.csv")
    print("  - exposure_network.csv")
    print("  - portfolio_transaction_stats.csv")
    print("  - counterparty_transaction_stats.csv")
    print()
    print("Next steps:")
    print("  1. Initialize databases: python backend/core/database_init.py")
    print("  2. Train ML models: cd ml-engine/training && ./train_all.sh")
    print("  3. Start backend: cd backend && uvicorn api.main:app --reload")
    print("  4. Start frontend: cd frontend && npm run dev")
    print()


if __name__ == '__main__':
    generate_all_data()

# Made with Bob
