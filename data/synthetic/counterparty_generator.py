"""
Counterparty Network Generator for AI Risk Constellation System
Generates synthetic counterparty network with relationships and credit ratings.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
import networkx as nx


class CounterpartyGenerator:
    """Generate synthetic counterparty network for testing and demonstration."""
    
    def __init__(self, num_counterparties=200, seed=42):
        """
        Initialize the counterparty generator.
        
        Args:
            num_counterparties: Number of counterparties to generate
            seed: Random seed for reproducibility
        """
        self.num_counterparties = num_counterparties
        self.seed = seed
        np.random.seed(seed)
        
        # Counterparty types
        self.entity_types = ['BANK', 'BROKER', 'HEDGE_FUND', 'INSURANCE', 'CORPORATE', 
                            'SOVEREIGN', 'PENSION', 'MUTUAL_FUND', 'PRIVATE_EQUITY', 'FAMILY_OFFICE']
        
        # Credit ratings
        self.credit_ratings = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 
                              'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 
                              'B+', 'B', 'B-', 'CCC', 'CC', 'C', 'D']
        
        # Geographic regions
        self.regions = ['NORTH_AMERICA', 'EUROPE', 'ASIA_PACIFIC', 'LATIN_AMERICA', 
                       'MIDDLE_EAST', 'AFRICA']
        
    def generate_counterparty_metadata(self):
        """
        Generate counterparty metadata.
        
        Returns:
            List of counterparty metadata dictionaries
        """
        counterparties = []
        
        for i in range(self.num_counterparties):
            counterparty_id = f"CP{str(i).zfill(4)}"
            entity_type = np.random.choice(self.entity_types)
            
            # Credit rating distribution (more higher ratings)
            rating_weights = np.exp(-np.arange(len(self.credit_ratings)) * 0.2)
            rating_weights = rating_weights / rating_weights.sum()
            credit_rating = np.random.choice(self.credit_ratings, p=rating_weights)
            
            # Credit score (0-100)
            rating_index = self.credit_ratings.index(credit_rating)
            credit_score = 100 - (rating_index * 5) + np.random.normal(0, 5)
            credit_score = np.clip(credit_score, 0, 100)
            
            # Probability of default based on rating
            pd_1y = 0.0001 * np.exp(rating_index * 0.3) + np.random.uniform(0, 0.001)
            
            # Total exposure (log-normal distribution)
            total_exposure = np.random.lognormal(17, 1.5)  # Mean ~$30M
            
            # Assets under management / total assets
            if entity_type in ['HEDGE_FUND', 'MUTUAL_FUND', 'PENSION', 'PRIVATE_EQUITY']:
                aum = np.random.lognormal(19, 2)  # Mean ~$150M
            else:
                aum = np.random.lognormal(20, 2.5)  # Mean ~$500M
            
            # Leverage ratio
            if entity_type in ['HEDGE_FUND', 'PRIVATE_EQUITY']:
                leverage = np.random.uniform(2, 8)
            elif entity_type in ['BANK', 'BROKER']:
                leverage = np.random.uniform(10, 30)
            else:
                leverage = np.random.uniform(1, 3)
            
            # Liquidity metrics
            liquidity_ratio = np.random.uniform(0.1, 0.5)
            
            # Geographic region
            region = np.random.choice(self.regions)
            
            # Systemic importance score (0-100)
            systemic_importance = np.random.beta(2, 5) * 100
            if entity_type in ['BANK', 'SOVEREIGN']:
                systemic_importance += 20
            systemic_importance = np.clip(systemic_importance, 0, 100)
            
            counterparties.append({
                'counterparty_id': counterparty_id,
                'counterparty_name': f"{entity_type.replace('_', ' ').title()} {i+1}",
                'entity_type': entity_type,
                'credit_rating': credit_rating,
                'credit_score': credit_score,
                'pd_1y': pd_1y,  # Probability of default (1 year)
                'total_exposure': total_exposure,
                'aum': aum,
                'leverage_ratio': leverage,
                'liquidity_ratio': liquidity_ratio,
                'region': region,
                'systemic_importance': systemic_importance,
                'is_systemically_important': systemic_importance > 70,
                'last_updated': pd.Timestamp.now()
            })
        
        return counterparties
    
    def generate_relationship_network(self, counterparty_metadata):
        """
        Generate relationship network between counterparties.
        
        Args:
            counterparty_metadata: List of counterparty metadata
            
        Returns:
            DataFrame with relationships and NetworkX graph
        """
        relationships = []
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes
        for cp in counterparty_metadata:
            G.add_node(cp['counterparty_id'], **cp)
        
        # Generate relationships (edges)
        # More connected counterparties have higher probability of relationships
        num_relationships = int(self.num_counterparties * 2.5)  # Average degree ~5
        
        for _ in range(num_relationships):
            # Select two random counterparties
            cp1, cp2 = np.random.choice(self.num_counterparties, size=2, replace=False)
            cp1_id = f"CP{str(cp1).zfill(4)}"
            cp2_id = f"CP{str(cp2).zfill(4)}"
            
            # Skip if relationship already exists
            if G.has_edge(cp1_id, cp2_id):
                continue
            
            # Relationship type
            relationship_types = ['TRADING_PARTNER', 'LENDER_BORROWER', 'PARENT_SUBSIDIARY',
                                'JOINT_VENTURE', 'STRATEGIC_ALLIANCE', 'CLEARING_MEMBER']
            relationship_type = np.random.choice(relationship_types)
            
            # Exposure amount
            exposure_amount = np.random.lognormal(15, 2)  # Mean ~$3M
            
            # Relationship strength (0-1)
            strength = np.random.beta(2, 5)
            
            # Correlation coefficient
            correlation = np.random.uniform(-0.3, 0.8)
            
            # Add edge to graph
            G.add_edge(cp1_id, cp2_id, 
                      relationship_type=relationship_type,
                      exposure_amount=exposure_amount,
                      strength=strength,
                      correlation=correlation)
            
            relationships.append({
                'counterparty_1': cp1_id,
                'counterparty_2': cp2_id,
                'relationship_type': relationship_type,
                'exposure_amount': exposure_amount,
                'strength': strength,
                'correlation': correlation,
                'bidirectional': True
            })
        
        return pd.DataFrame(relationships), G
    
    def calculate_network_metrics(self, G, counterparty_metadata):
        """
        Calculate network centrality metrics.
        
        Args:
            G: NetworkX graph
            counterparty_metadata: List of counterparty metadata
            
        Returns:
            DataFrame with network metrics
        """
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        
        # PageRank
        pagerank = nx.pagerank(G)
        
        metrics = []
        
        for cp in counterparty_metadata:
            cp_id = cp['counterparty_id']
            
            # Get centrality metrics
            degree = degree_centrality.get(cp_id, 0)
            betweenness = betweenness_centrality.get(cp_id, 0)
            closeness = closeness_centrality.get(cp_id, 0)
            eigenvector = eigenvector_centrality.get(cp_id, 0)
            pr = pagerank.get(cp_id, 0)
            
            # Calculate contagion risk (combination of centrality and credit risk)
            contagion_risk = (
                0.3 * degree + 
                0.2 * betweenness + 
                0.2 * eigenvector + 
                0.3 * (1 - cp['credit_score'] / 100)
            ) * 100
            
            metrics.append({
                'counterparty_id': cp_id,
                'degree_centrality': degree,
                'betweenness_centrality': betweenness,
                'closeness_centrality': closeness,
                'eigenvector_centrality': eigenvector,
                'pagerank': pr,
                'num_connections': G.degree(cp_id),
                'contagion_risk_score': contagion_risk,
                'network_cluster': 0  # Will be calculated separately
            })
        
        # Detect communities
        communities = nx.community.greedy_modularity_communities(G)
        for i, community in enumerate(communities):
            for node in community:
                for metric in metrics:
                    if metric['counterparty_id'] == node:
                        metric['network_cluster'] = i
                        break
        
        return pd.DataFrame(metrics)
    
    def generate_all(self, output_dir='data/synthetic'):
        """
        Generate all counterparty data and save to files.
        
        Args:
            output_dir: Directory to save generated data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating {self.num_counterparties} counterparties...")
        
        # Generate counterparty metadata
        counterparty_metadata = self.generate_counterparty_metadata()
        
        # Generate relationship network
        print("Generating relationship network...")
        relationships_df, G = self.generate_relationship_network(counterparty_metadata)
        
        # Calculate network metrics
        print("Calculating network metrics...")
        network_metrics_df = self.calculate_network_metrics(G, counterparty_metadata)
        
        # Save to CSV and JSON
        print("Saving data to files...")
        relationships_df.to_csv(output_path / 'counterparty_relationships.csv', index=False)
        network_metrics_df.to_csv(output_path / 'counterparty_network_metrics.csv', index=False)
        
        # Save metadata
        with open(output_path / 'counterparty_metadata.json', 'w') as f:
            # Convert Timestamp to string for JSON serialization
            for cp in counterparty_metadata:
                cp['last_updated'] = str(cp['last_updated'])
            json.dump(counterparty_metadata, f, indent=2)
        
        # Save network graph
        nx.write_gexf(G, output_path / 'counterparty_network.gexf')
        
        print(f"✅ Counterparty data generation complete!")
        print(f"   - {self.num_counterparties} counterparties")
        print(f"   - {len(relationships_df)} relationships")
        print(f"   - Average connections per counterparty: {len(relationships_df) * 2 / self.num_counterparties:.1f}")
        print(f"   - Network density: {nx.density(G):.3f}")
        
        return counterparty_metadata, relationships_df, network_metrics_df, G


if __name__ == '__main__':
    # Generate counterparty data
    generator = CounterpartyGenerator(
        num_counterparties=200,
        seed=42
    )
    
    generator.generate_all()

# Made with Bob
