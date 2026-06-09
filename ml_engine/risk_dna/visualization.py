"""
Risk DNA Visualization
Utilities for visualizing Risk DNA fingerprints and relationships.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional, Tuple
import logging

from .dna_generator import RiskDNA
from .dna_comparator import DNAComparator

logger = logging.getLogger(__name__)


class DNAVisualizer:
    """
    Visualizes Risk DNA fingerprints.
    """
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize visualizer.
        
        Args:
            figsize: Figure size for plots
        """
        self.figsize = figsize
        sns.set_style('whitegrid')
        logger.info("Initialized DNAVisualizer")
    
    def plot_dna_vector(self, dna: RiskDNA, save_path: Optional[str] = None):
        """
        Plot DNA vector as bar chart.
        
        Args:
            dna: Risk DNA to visualize
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Plot vector values
        ax.bar(range(len(dna.dna_vector)), dna.dna_vector, alpha=0.7)
        ax.set_xlabel('DNA Dimension')
        ax.set_ylabel('Value')
        ax.set_title(f'Risk DNA Vector - {dna.entity_id}')
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved DNA vector plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_dna_components(self, dna: RiskDNA, save_path: Optional[str] = None):
        """
        Plot DNA components as pie chart.
        
        Args:
            dna: Risk DNA to visualize
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Extract components
        labels = list(dna.components.keys())
        values = list(dna.components.values())
        
        # Create pie chart
        colors = sns.color_palette('husl', len(labels))
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f'Risk DNA Components - {dna.entity_id}')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved components plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_dna_heatmap(self, dna_list: List[RiskDNA], 
                        labels: Optional[List[str]] = None,
                        save_path: Optional[str] = None):
        """
        Plot heatmap of DNA vectors.
        
        Args:
            dna_list: List of Risk DNAs
            labels: Labels for each DNA
            save_path: Path to save figure
        """
        # Stack DNA vectors
        vectors = np.array([dna.dna_vector for dna in dna_list])
        
        # Create labels if not provided
        if labels is None:
            labels = [dna.entity_id for dna in dna_list]
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sns.heatmap(vectors, cmap='RdYlBu_r', center=0, 
                   yticklabels=labels, cbar_kws={'label': 'DNA Value'},
                   ax=ax)
        
        ax.set_xlabel('DNA Dimension')
        ax.set_ylabel('Entity')
        ax.set_title('Risk DNA Heatmap')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved heatmap to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_similarity_matrix(self, dna_list: List[RiskDNA],
                               labels: Optional[List[str]] = None,
                               save_path: Optional[str] = None):
        """
        Plot similarity matrix between DNAs.
        
        Args:
            dna_list: List of Risk DNAs
            labels: Labels for each DNA
            save_path: Path to save figure
        """
        # Compute similarity matrix
        comparator = DNAComparator(metric='cosine')
        similarity_matrix = comparator.compare_batch(dna_list)
        
        # Create labels if not provided
        if labels is None:
            labels = [dna.entity_id for dna in dna_list]
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sns.heatmap(similarity_matrix, annot=True, fmt='.2f', 
                   cmap='YlGnBu', vmin=0, vmax=1,
                   xticklabels=labels, yticklabels=labels,
                   cbar_kws={'label': 'Similarity'},
                   ax=ax)
        
        ax.set_title('Risk DNA Similarity Matrix')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved similarity matrix to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_evolution_trajectory(self, dna_list: List[RiskDNA],
                                 save_path: Optional[str] = None):
        """
        Plot DNA evolution trajectory over time.
        
        Args:
            dna_list: List of Risk DNAs ordered by time
            save_path: Path to save figure
        """
        # Sort by timestamp
        dna_list = sorted(dna_list, key=lambda x: x.timestamp)
        
        # Extract timestamps and vectors
        timestamps = [dna.timestamp for dna in dna_list]
        vectors = np.array([dna.dna_vector for dna in dna_list])
        
        # Plot first few dimensions
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        axes = axes.flatten()
        
        for i, ax in enumerate(axes):
            if i < vectors.shape[1]:
                ax.plot(timestamps, vectors[:, i], marker='o', linewidth=2)
                ax.set_xlabel('Time')
                ax.set_ylabel(f'DNA Dim {i}')
                ax.set_title(f'Dimension {i} Evolution')
                ax.grid(True, alpha=0.3)
        
        plt.suptitle(f'Risk DNA Evolution - {dna_list[0].entity_id}')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved evolution trajectory to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_component_evolution(self, dna_list: List[RiskDNA],
                                save_path: Optional[str] = None):
        """
        Plot evolution of DNA components over time.
        
        Args:
            dna_list: List of Risk DNAs ordered by time
            save_path: Path to save figure
        """
        # Sort by timestamp
        dna_list = sorted(dna_list, key=lambda x: x.timestamp)
        
        # Extract timestamps and components
        timestamps = [dna.timestamp for dna in dna_list]
        
        # Get all component keys
        component_keys = list(dna_list[0].components.keys())
        
        # Create subplots
        n_components = len(component_keys)
        n_cols = 2
        n_rows = (n_components + 1) // 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=self.figsize)
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        axes = axes.flatten()
        
        for i, key in enumerate(component_keys):
            values = [dna.components.get(key, 0) for dna in dna_list]
            axes[i].plot(timestamps, values, marker='o', linewidth=2)
            axes[i].set_xlabel('Time')
            axes[i].set_ylabel('Value')
            axes[i].set_title(key.replace('_', ' ').title())
            axes[i].grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(n_components, len(axes)):
            axes[i].axis('off')
        
        plt.suptitle(f'Component Evolution - {dna_list[0].entity_id}')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved component evolution to {save_path}")
        else:
            plt.show()
        
        plt.close()


class NetworkVisualizer:
    """
    Visualizes similarity networks between Risk DNAs.
    """
    
    def __init__(self):
        """Initialize network visualizer."""
        logger.info("Initialized NetworkVisualizer")
    
    def plot_similarity_network(self, dna_list: List[RiskDNA],
                               threshold: float = 0.7,
                               save_path: Optional[str] = None):
        """
        Plot network graph of similar DNAs.
        
        Args:
            dna_list: List of Risk DNAs
            threshold: Similarity threshold for edges
            save_path: Path to save figure
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("NetworkX not installed, skipping network visualization")
            return
        
        # Compute similarity matrix
        comparator = DNAComparator(metric='cosine')
        similarity_matrix = comparator.compare_batch(dna_list)
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes
        for i, dna in enumerate(dna_list):
            G.add_node(i, label=dna.entity_id)
        
        # Add edges above threshold
        for i in range(len(dna_list)):
            for j in range(i+1, len(dna_list)):
                if similarity_matrix[i, j] >= threshold:
                    G.add_edge(i, j, weight=similarity_matrix[i, j])
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 10))
        
        pos = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue',
                              alpha=0.9, ax=ax)
        
        # Draw edges
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        nx.draw_networkx_edges(G, pos, width=[w*3 for w in weights],  # type: ignore
                              alpha=0.5, ax=ax)
        
        # Draw labels
        labels = {i: dna.entity_id for i, dna in enumerate(dna_list)}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, ax=ax)
        
        ax.set_title(f'Risk DNA Similarity Network (threshold={threshold})')
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved similarity network to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_cluster_network(self, dna_list: List[RiskDNA],
                            cluster_labels: np.ndarray,
                            save_path: Optional[str] = None):
        """
        Plot network with cluster coloring.
        
        Args:
            dna_list: List of Risk DNAs
            cluster_labels: Cluster assignments
            save_path: Path to save figure
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("NetworkX not installed, skipping cluster network visualization")
            return
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes with cluster info
        for i, (dna, label) in enumerate(zip(dna_list, cluster_labels)):
            G.add_node(i, label=dna.entity_id, cluster=int(label))
        
        # Add edges within clusters
        for i in range(len(dna_list)):
            for j in range(i+1, len(dna_list)):
                if cluster_labels[i] == cluster_labels[j]:
                    G.add_edge(i, j)
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 10))
        
        pos = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Color by cluster
        unique_clusters = set(cluster_labels)
        colors = sns.color_palette('husl', len(unique_clusters))
        color_map = {cluster: colors[i] for i, cluster in enumerate(unique_clusters)}
        
        node_colors = [color_map[cluster_labels[i]] for i in range(len(dna_list))]
        
        # Draw
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color=node_colors,  # type: ignore
                              alpha=0.9, ax=ax)
        nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
        
        labels = {i: dna.entity_id for i, dna in enumerate(dna_list)}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, ax=ax)
        
        ax.set_title('Risk DNA Cluster Network')
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved cluster network to {save_path}")
        else:
            plt.show()
        
        plt.close()


if __name__ == '__main__':
    # Example usage
    print("Risk DNA Visualization Module")
    
    from dna_generator import RiskDNAGenerator
    
    # Create generator
    generator = RiskDNAGenerator(dna_dim=256)
    
    # Generate sample DNAs
    dnas = []
    for i in range(5):
        features = {
            'portfolio': {'total_value': 1000000 * (i + 1)},
            'historical': {'volatility_30d': 0.1 + i * 0.02},
            'counterparty': {'num_counterparties': 10 + i * 2},
            'market': {'vix_level': 15 + i}
        }
        dna = generator.generate(f'ENTITY_{i:03d}', features)
        dnas.append(dna)
    
    # Create visualizer
    visualizer = DNAVisualizer()
    
    print("Visualizer initialized")
    print("Use visualizer.plot_dna_vector(dna) to visualize a DNA")
    print("Use visualizer.plot_similarity_matrix(dnas) to see similarities")

# Made with Bob
