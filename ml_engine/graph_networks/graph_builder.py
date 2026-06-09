"""
Graph Builder for Risk Networks
Converts counterparty and transaction data to PyTorch Geometric graph format.
"""

import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data, HeteroData
from typing import Dict, List, Tuple, Optional, Union
import logging

logger = logging.getLogger(__name__)


class RiskGraphBuilder:
    """
    Builds graph representations from counterparty and transaction data.
    """
    
    def __init__(self, node_feature_columns: Optional[List[str]] = None,
                 edge_feature_columns: Optional[List[str]] = None):
        """
        Initialize graph builder.
        
        Args:
            node_feature_columns: List of column names for node features
            edge_feature_columns: List of column names for edge features
        """
        self.node_feature_columns = node_feature_columns or [
            'credit_score', 'total_exposure', 'leverage_ratio',
            'liquidity_ratio', 'systemic_importance'
        ]
        
        self.edge_feature_columns = edge_feature_columns or [
            'exposure_amount', 'strength', 'correlation'
        ]
        
        self.node_id_to_idx = {}
        self.idx_to_node_id = {}
        
        logger.info("Initialized RiskGraphBuilder")
    
    def build_from_dataframes(self, 
                             nodes_df: pd.DataFrame,
                             edges_df: pd.DataFrame,
                             node_id_col: str = 'counterparty_id',
                             source_col: str = 'counterparty_1',
                             target_col: str = 'counterparty_2') -> Data:
        """
        Build PyG graph from pandas DataFrames.
        
        Args:
            nodes_df: DataFrame with node information
            edges_df: DataFrame with edge information
            node_id_col: Column name for node IDs
            source_col: Column name for source nodes in edges
            target_col: Column name for target nodes in edges
            
        Returns:
            PyTorch Geometric Data object
        """
        # Create node ID mapping
        unique_nodes = nodes_df[node_id_col].unique()
        self.node_id_to_idx = {node_id: idx for idx, node_id in enumerate(unique_nodes)}
        self.idx_to_node_id = {idx: node_id for node_id, idx in self.node_id_to_idx.items()}
        
        # Extract node features
        node_features = self._extract_node_features(nodes_df, node_id_col)
        
        # Extract edge indices and features
        edge_index, edge_features = self._extract_edges(
            edges_df, source_col, target_col
        )
        
        # Create PyG Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            edge_attr=edge_features,
            num_nodes=len(unique_nodes)
        )
        
        # Add metadata
        data.node_ids = list(unique_nodes)
        data.node_id_to_idx = self.node_id_to_idx
        
        logger.info(f"Built graph with {data.num_nodes} nodes and {data.edge_index.shape[1]} edges")
        
        return data
    
    def _extract_node_features(self, nodes_df: pd.DataFrame,
                               node_id_col: str) -> torch.Tensor:
        """
        Extract node features from DataFrame.
        
        Args:
            nodes_df: DataFrame with node information
            node_id_col: Column name for node IDs
            
        Returns:
            Node feature tensor [num_nodes, num_features]
        """
        # Sort by node ID to match mapping
        nodes_df = nodes_df.set_index(node_id_col)
        nodes_df = nodes_df.loc[self.idx_to_node_id.values()]
        
        # Extract features
        available_cols = [col for col in self.node_feature_columns if col in nodes_df.columns]
        
        if not available_cols:
            logger.warning("No node feature columns found, using default features")
            # Create default features
            num_nodes = len(nodes_df)
            features = np.random.randn(num_nodes, 5)
        else:
            features = nodes_df[available_cols].values
        
        # Handle missing values
        features = np.nan_to_num(features, nan=0.0)
        
        # Normalize features
        features = self._normalize_features(features)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def _extract_edges(self, edges_df: pd.DataFrame,
                      source_col: str, target_col: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract edge indices and features.
        
        Args:
            edges_df: DataFrame with edge information
            source_col: Source node column
            target_col: Target node column
            
        Returns:
            Tuple of (edge_index, edge_features)
        """
        # Map node IDs to indices
        source_indices = edges_df[source_col].map(self.node_id_to_idx)
        target_indices = edges_df[target_col].map(self.node_id_to_idx)
        
        # Remove edges with unmapped nodes
        valid_mask = source_indices.notna() & target_indices.notna()
        source_indices = source_indices[valid_mask].astype(int)
        target_indices = target_indices[valid_mask].astype(int)
        
        # Create edge index (bidirectional)
        edge_index = torch.tensor(
            np.array([
                np.concatenate([source_indices, target_indices]),
                np.concatenate([target_indices, source_indices])
            ]),
            dtype=torch.long
        )
        
        # Extract edge features
        available_cols = [col for col in self.edge_feature_columns if col in edges_df.columns]
        
        if not available_cols:
            logger.warning("No edge feature columns found, using default features")
            num_edges = len(source_indices)
            edge_features = np.random.randn(num_edges * 2, 3)  # *2 for bidirectional
        else:
            edge_features = edges_df.loc[valid_mask, available_cols].values
            # Duplicate for bidirectional edges
            edge_features = np.concatenate([edge_features, edge_features], axis=0)
        
        # Handle missing values
        edge_features = np.nan_to_num(edge_features, nan=0.0)
        
        # Normalize features
        edge_features = self._normalize_features(edge_features)
        
        return edge_index, torch.tensor(edge_features, dtype=torch.float32)
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """
        Normalize features using standardization.
        
        Args:
            features: Feature array
            
        Returns:
            Normalized features
        """
        mean = features.mean(axis=0, keepdims=True)
        std = features.std(axis=0, keepdims=True)
        std[std == 0] = 1.0  # Avoid division by zero
        
        return (features - mean) / std
    
    def add_temporal_edges(self, data: Data, 
                          temporal_edges_df: pd.DataFrame,
                          time_col: str = 'timestamp') -> Data:
        """
        Add temporal information to edges.
        
        Args:
            data: Existing graph data
            temporal_edges_df: DataFrame with temporal edge information
            time_col: Column name for timestamps
            
        Returns:
            Updated Data object with temporal features
        """
        # Convert timestamps to relative time features
        if time_col in temporal_edges_df.columns:
            timestamps = pd.to_datetime(temporal_edges_df[time_col])
            min_time = timestamps.min()
            relative_times = (timestamps - min_time).dt.total_seconds()
            
            # Normalize to [0, 1]
            relative_times = relative_times / relative_times.max()
            
            # Add as edge feature
            time_features = torch.tensor(relative_times.values, dtype=torch.float32).unsqueeze(1)
            
            if data.edge_attr is not None:
                # Duplicate for bidirectional edges
                time_features = torch.cat([time_features, time_features], dim=0)
                data.edge_attr = torch.cat([data.edge_attr, time_features], dim=1)
            else:
                data.edge_attr = time_features
        
        return data
    
    def create_subgraph(self, data: Data, node_indices: List[int]) -> Data:
        """
        Create subgraph from selected nodes.
        
        Args:
            data: Full graph data
            node_indices: Indices of nodes to include
            
        Returns:
            Subgraph Data object
        """
        node_indices = torch.tensor(node_indices, dtype=torch.long)
        
        # Extract node features
        x = data.x[node_indices]
        
        # Find edges within subgraph
        edge_mask = torch.isin(data.edge_index[0], node_indices) & \
                   torch.isin(data.edge_index[1], node_indices)
        
        edge_index = data.edge_index[:, edge_mask]
        
        # Remap node indices
        node_mapping = {int(old_idx): new_idx for new_idx, old_idx in enumerate(node_indices)}
        edge_index_remapped = torch.tensor([
            [node_mapping[int(idx.item())] for idx in edge_index[0]],
            [node_mapping[int(idx.item())] for idx in edge_index[1]]
        ], dtype=torch.long)
        
        # Extract edge features
        edge_attr = data.edge_attr[edge_mask] if data.edge_attr is not None else None
        
        subgraph = Data(
            x=x,
            edge_index=edge_index_remapped,
            edge_attr=edge_attr,
            num_nodes=len(node_indices)
        )
        
        return subgraph
    
    def to_networkx(self, data: Data):
        """
        Convert PyG Data to NetworkX graph.
        
        Args:
            data: PyG Data object
            
        Returns:
            NetworkX graph
        """
        import networkx as nx
        
        G = nx.Graph()
        
        # Add nodes
        for i in range(data.num_nodes):
            node_id = self.idx_to_node_id.get(i, i)
            G.add_node(node_id, features=data.x[i].numpy())
        
        # Add edges
        edge_index = data.edge_index.numpy()
        for i in range(edge_index.shape[1]):
            src = self.idx_to_node_id.get(edge_index[0, i], edge_index[0, i])
            dst = self.idx_to_node_id.get(edge_index[1, i], edge_index[1, i])
            
            if data.edge_attr is not None:
                edge_features = data.edge_attr[i].numpy()
                G.add_edge(src, dst, features=edge_features)
            else:
                G.add_edge(src, dst)
        
        return G


class DynamicGraphBuilder:
    """
    Builder for dynamic/temporal graphs with time-varying structure.
    """
    
    def __init__(self, time_window: int = 30):
        """
        Initialize dynamic graph builder.
        
        Args:
            time_window: Time window for graph snapshots (in days)
        """
        self.time_window = time_window
        self.static_builder = RiskGraphBuilder()
    
    def build_temporal_snapshots(self,
                                 nodes_df: pd.DataFrame,
                                 edges_df: pd.DataFrame,
                                 time_col: str = 'date',
                                 num_snapshots: int = 10) -> List[Data]:
        """
        Build sequence of graph snapshots over time.
        
        Args:
            nodes_df: Node DataFrame
            edges_df: Edge DataFrame with timestamps
            time_col: Column name for timestamps
            num_snapshots: Number of temporal snapshots
            
        Returns:
            List of Data objects (one per snapshot)
        """
        # Sort edges by time
        edges_df = edges_df.sort_values(time_col)
        
        # Determine time range
        min_time = pd.to_datetime(edges_df[time_col].min())
        max_time = pd.to_datetime(edges_df[time_col].max())
        time_range = (max_time - min_time).days
        
        snapshot_interval = time_range / num_snapshots
        
        snapshots = []
        for i in range(num_snapshots):
            # Define time window
            start_time = min_time + pd.Timedelta(days=i * snapshot_interval)
            end_time = start_time + pd.Timedelta(days=self.time_window)
            
            # Filter edges in time window
            mask = (pd.to_datetime(edges_df[time_col]) >= start_time) & \
                   (pd.to_datetime(edges_df[time_col]) < end_time)
            snapshot_edges = edges_df[mask]
            
            if len(snapshot_edges) > 0:
                # Build graph for this snapshot
                data = self.static_builder.build_from_dataframes(
                    nodes_df, snapshot_edges
                )
                data.timestamp = start_time
                snapshots.append(data)
        
        logger.info(f"Built {len(snapshots)} temporal snapshots")
        
        return snapshots


if __name__ == '__main__':
    # Example usage
    import pandas as pd
    
    # Create sample data
    nodes_df = pd.DataFrame({
        'counterparty_id': [f'CP{i:04d}' for i in range(10)],
        'credit_score': np.random.uniform(50, 100, 10),
        'total_exposure': np.random.lognormal(15, 1, 10),
        'leverage_ratio': np.random.uniform(1, 5, 10),
        'liquidity_ratio': np.random.uniform(0.1, 0.5, 10),
        'systemic_importance': np.random.uniform(0, 100, 10)
    })
    
    edges_df = pd.DataFrame({
        'counterparty_1': [f'CP{i:04d}' for i in np.random.randint(0, 10, 20)],
        'counterparty_2': [f'CP{i:04d}' for i in np.random.randint(0, 10, 20)],
        'exposure_amount': np.random.lognormal(14, 1, 20),
        'strength': np.random.uniform(0, 1, 20),
        'correlation': np.random.uniform(-0.3, 0.8, 20)
    })
    
    # Build graph
    builder = RiskGraphBuilder()
    data = builder.build_from_dataframes(nodes_df, edges_df)
    
    print(f"Graph built:")
    print(f"  Nodes: {data.num_nodes}")
    print(f"  Edges: {data.edge_index.shape[1]}")
    print(f"  Node features: {data.x.shape}")
    print(f"  Edge features: {data.edge_attr.shape}")

# Made with Bob
