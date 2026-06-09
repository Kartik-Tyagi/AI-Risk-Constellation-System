"""
Market Data Generator for AI Risk Constellation System
Generates synthetic stock market data including prices, volatility, volume, and indicators.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path


class MarketDataGenerator:
    """Generate synthetic market data for testing and demonstration."""
    
    def __init__(self, num_tickers=100, start_date='2022-01-01', end_date='2024-12-31', seed=42):
        """
        Initialize the market data generator.
        
        Args:
            num_tickers: Number of stock tickers to generate
            start_date: Start date for time series
            end_date: End date for time series
            seed: Random seed for reproducibility
        """
        self.num_tickers = num_tickers
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.seed = seed
        np.random.seed(seed)
        
        # Generate ticker symbols
        self.tickers = self._generate_tickers()
        
        # Generate date range (business days only)
        self.dates = pd.bdate_range(start=self.start_date, end=self.end_date)
        
    def _generate_tickers(self):
        """Generate realistic ticker symbols."""
        sectors = ['TECH', 'FIN', 'HLTH', 'ENRG', 'CONS', 'IND', 'MAT', 'UTIL', 'REAL', 'COMM']
        tickers = []
        
        for i in range(self.num_tickers):
            sector = sectors[i % len(sectors)]
            num = str(i).zfill(3)
            tickers.append(f"{sector}{num}")
            
        return tickers
    
    def generate_price_series(self, ticker, initial_price: float = 100.0, drift: float = 0.0001, volatility: float = 0.02):
        """
        Generate price series using geometric Brownian motion.
        
        Args:
            ticker: Stock ticker symbol
            initial_price: Starting price
            drift: Daily drift (trend)
            volatility: Daily volatility
            
        Returns:
            DataFrame with OHLCV data
        """
        n_days = len(self.dates)
        
        # Generate returns using geometric Brownian motion
        returns = np.random.normal(drift, volatility, n_days)
        
        # Add some autocorrelation for realism
        for i in range(1, n_days):
            returns[i] += 0.1 * returns[i-1]
        
        # Calculate prices
        prices = initial_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC from close prices
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
        open_price = np.roll(prices, 1)
        open_price[0] = initial_price
        
        # Generate volume (log-normal distribution)
        volume = np.random.lognormal(15, 1, n_days).astype(int)
        
        # Create DataFrame
        df = pd.DataFrame({
            'ticker': ticker,
            'date': self.dates,
            'open': open_price,
            'high': high,
            'low': low,
            'close': prices,
            'volume': volume
        })
        
        return df
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators and risk metrics.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicators
        """
        # Returns
        df['returns'] = df['close'].pct_change()
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Volatility (20-day rolling)
        df['volatility_20'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Price momentum
        df['momentum_10'] = df['close'].pct_change(periods=10)
        df['momentum_30'] = df['close'].pct_change(periods=30)
        
        # Bollinger Bands
        df['bb_middle'] = df['sma_20']
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (2 * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (2 * df['bb_std'])
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def generate_market_conditions(self):
        """
        Generate overall market condition indicators.
        
        Returns:
            DataFrame with market-wide indicators
        """
        market_data = []
        
        for date in self.dates:
            # Market regime (bull/bear/neutral)
            regime_prob = np.random.random()
            if regime_prob < 0.3:
                regime = 'bull'
                market_return = np.random.normal(0.001, 0.01)
            elif regime_prob < 0.6:
                regime = 'neutral'
                market_return = np.random.normal(0, 0.008)
            else:
                regime = 'bear'
                market_return = np.random.normal(-0.001, 0.015)
            
            # VIX-like volatility index
            vix = np.random.lognormal(2.8, 0.5)
            
            # Market breadth
            advancing = np.random.randint(40, 60)
            declining = 100 - advancing
            
            market_data.append({
                'date': date,
                'regime': regime,
                'market_return': market_return,
                'vix': vix,
                'advancing': advancing,
                'declining': declining,
                'market_cap_weighted_return': market_return * np.random.uniform(0.8, 1.2)
            })
        
        return pd.DataFrame(market_data)
    
    def generate_all(self, output_dir='data/synthetic'):
        """
        Generate all market data and save to files.
        
        Args:
            output_dir: Directory to save generated data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating market data for {self.num_tickers} tickers...")
        
        # Generate price data for all tickers
        all_prices = []
        ticker_metadata = []
        
        for i, ticker in enumerate(self.tickers):
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{self.num_tickers} tickers...")
            
            # Vary initial prices and characteristics
            initial_price = np.random.uniform(10, 500)
            drift = np.random.normal(0.0001, 0.0002)
            volatility = np.random.uniform(0.015, 0.035)
            
            # Generate price series
            df = self.generate_price_series(ticker, initial_price, drift, volatility)
            df = self.calculate_indicators(df)
            all_prices.append(df)
            
            # Store metadata
            sector = ticker[:4]
            ticker_metadata.append({
                'ticker': ticker,
                'sector': sector,
                'initial_price': initial_price,
                'avg_volatility': volatility,
                'market_cap': np.random.lognormal(20, 2)  # Billions
            })
        
        # Combine all price data
        prices_df = pd.concat(all_prices, ignore_index=True)
        
        # Generate market conditions
        print("Generating market conditions...")
        market_conditions = self.generate_market_conditions()
        
        # Save to CSV
        print("Saving data to CSV files...")
        prices_df.to_csv(output_path / 'market_prices.csv', index=False)
        market_conditions.to_csv(output_path / 'market_conditions.csv', index=False)
        
        # Save metadata to JSON
        with open(output_path / 'ticker_metadata.json', 'w') as f:
            json.dump(ticker_metadata, f, indent=2)
        
        print(f"✅ Market data generation complete!")
        print(f"   - {len(prices_df)} price records")
        print(f"   - {len(market_conditions)} market condition records")
        print(f"   - {len(ticker_metadata)} tickers")
        print(f"   - Date range: {self.start_date.date()} to {self.end_date.date()}")
        
        return prices_df, market_conditions, ticker_metadata


if __name__ == '__main__':
    # Generate market data
    generator = MarketDataGenerator(
        num_tickers=100,
        start_date='2022-01-01',
        end_date='2024-12-31',
        seed=42
    )
    
    generator.generate_all()

# Made with Bob
