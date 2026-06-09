"""
Risk Propagation Graph Attention Network
Custom GAT variant specifically designed for modeling risk propagation through counterparty networks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import softmax
from typing import Optional, Tuple, Dict
import logging

from .gat_model import GAT, GATConv

logger = logging.getLogger(__name__)


class RiskPropagationGAT(nn.Module):
    """
    Graph Attention Network specialized for risk propagation modeling.
    
    Node features: Entity risk metrics (credit score, exposure, leverage, etc.)
    Edge features: Exposure amounts, relationship types, correlation
    Output: Propagated risk scores per node
    """
    
    def __init__(self, node_feature_dim: int, edge_feature_dim: int,
                 hidden_dim: int = 128, output_dim: int = 64,
                 num_layers: int = 3, heads: int = 4,
                 dropout: float = 0.3, use_edge_features: bool = True):
        """
        Initialize Risk Propagation GAT.
        
        Args:
            node_feature_dim: Dimension of node features
            edge_feature_dim: Dimension of edge features
            hidden_dim: Hidden layer dimension
            output_dim: Output embedding dimension
            num_layers: Number of GAT layers
            heads: Number of attention heads
            dropout: Dropout probability
            use_edge_features: Whether to use edge features in attention
        """
        super(RiskPropagationGAT, self).__init__()
        
        self.node_feature_dim = node_feature_dim
        self.edge_feature_dim = edge_feature_dim
        self.use_edge_features = use_edge_features
        
        # Input projection
        self.node_encoder = nn.Linear(node_feature_dim, hidden_dim)
        
        if use_edge_features:
            self.edge_encoder = nn.Linear(edge_feature_dim, hidden_dim)
        
        # GAT layers
        self.gat = GAT(
            in_channels=hidden_dim,
            hidden_channels=hidden_dim,
            out_channels=output_dim,
            num_layers=num_layers,
            heads=heads,
            dropout=dropout
        )
        
        # Risk score predictor
        self.risk_predictor = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Risk score between 0 and 1
        )
        
        # Systemic risk aggregator
        self.systemic_aggregator = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        logger.info(f"Initialized RiskPropagationGAT with {num_layers} layers, {heads} heads")
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None,
                return_attention: bool = False) -> Dict[str, torch.Tensor]:
        """
        Forward pass for risk propagation.
        
        Args:
            x: Node features [num_nodes, node_feature_dim]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge features [num_edges, edge_feature_dim]
            return_attention: Whether to return attention weights
            
        Returns:
            Dictionary containing:
                - node_embeddings: Node embeddings [num_nodes, output_dim]
                - risk_scores: Risk scores per node [num_nodes, 1]
                - systemic_risk: Global systemic risk score [1]
                - attention_weights: (optional) Attention weights
        """
        # Encode node features
        x_encoded = self.node_encoder(x)
        x_encoded = F.relu(x_encoded)
        
        # Encode edge features if provided
        if self.use_edge_features and edge_attr is not None:
            edge_attr_encoded = self.edge_encoder(edge_attr)
            edge_attr_encoded = F.relu(edge_attr_encoded)
        else:
            edge_attr_encoded = None
        
        # Apply GAT
        if return_attention:
            node_embeddings, attention_weights = self.gat(
                x_encoded, edge_index, edge_attr_encoded,
                return_attention_weights=True
            )
        else:
            node_embeddings = self.gat(x_encoded, edge_index, edge_attr_encoded)
            attention_weights = None
        
        # Predict risk scores
        risk_scores = self.risk_predictor(node_embeddings)
        
        # Calculate systemic risk (global graph-level risk)
        systemic_features = torch.mean(node_embeddings, dim=0, keepdim=True)
        systemic_risk = self.systemic_aggregator(systemic_features)
        
        results = {
            'node_embeddings': node_embeddings,
            'risk_scores': risk_scores,
            'systemic_risk': systemic_risk
        }
        
        if return_attention:
            results['attention_weights'] = attention_weights
        
        return results
    
    def predict_cascade(self, x: torch.Tensor, edge_index: torch.Tensor,
                       edge_attr: Optional[torch.Tensor] = None,
                       source_nodes: Optional[torch.Tensor] = None,
                       threshold: float = 0.5) -> Dict[str, torch.Tensor]:
        """
        Predict risk cascade from source nodes.
        
        Args:
            x: Node features
            edge_index: Edge indices
            edge_attr: Edge features
            source_nodes: Indices of source nodes (if None, use high-risk nodes)
            threshold: Risk threshold for cascade
            
        Returns:
            Dictionary with cascade information
        """
        # Get risk scores
        results = self.forward(x, edge_index, edge_attr)
        risk_scores = results['risk_scores'].squeeze()
        
        # Identify source nodes if not provided
        if source_nodes is None:
            source_nodes = torch.where(risk_scores > threshold)[0]
        
        # Simulate cascade propagation
        affected_nodes = self._simulate_cascade(
            risk_scores, edge_index, source_nodes, threshold
        )
        
        return {
            'source_nodes': source_nodes,
            'affected_nodes': affected_nodes,
            'cascade_size': len(affected_nodes),
            'risk_scores': risk_scores
        }
    
    def _simulate_cascade(self, risk_scores: torch.Tensor,
                         edge_index: torch.Tensor,
                         source_nodes: torch.Tensor,
                         threshold: float) -> torch.Tensor:
        """
        Simulate risk cascade propagation.
        
        Args:
            risk_scores: Risk scores for all nodes
            edge_index: Edge indices
            source_nodes: Starting nodes for cascade
            threshold: Risk threshold
            
        Returns:
            Tensor of affected node indices
        """
        affected = set(source_nodes.tolist())
        queue = list(source_nodes.tolist())
        
        # Build adjacency list
        adj_list = {}
        for i in range(edge_index.shape[1]):
            src, dst = edge_index[0, i].item(), edge_index[1, i].item()
            if src not in adj_list:
                adj_list[src] = []
            adj_list[src].append(dst)
        
        # BFS cascade simulation
        while queue:
            node = queue.pop(0)
            
            if node in adj_list:
                for neighbor in adj_list[node]:
                    if neighbor not in affected:
                        # Check if neighbor's risk exceeds threshold
                        if risk_scores[neighbor] > threshold * 0.7:  # Slightly lower threshold for propagation
                            affected.add(neighbor)
                            queue.append(neighbor)
        
        return torch.tensor(list(affected), dtype=torch.long)


class RiskContagionLayer(MessagePassing):
    """
    Custom message passing layer for risk contagion modeling.
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 edge_dim: Optional[int] = None):
        """
        Initialize risk contagion layer.
        
        Args:
            in_channels: Input feature dimension
            out_channels: Output feature dimension
            edge_dim: Edge feature dimension
        """
        super(RiskContagionLayer, self).__init__(aggr='add', node_dim=0)
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # Message network
        self.message_net = nn.Sequential(
            nn.Linear(2 * in_channels + (edge_dim if edge_dim else 0), out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )
        
        # Update network
        self.update_net = nn.Sequential(
            nn.Linear(in_channels + out_channels, out_channels),
            nn.ReLU(),
            nn.Linear(out_channels, out_channels)
        )
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge features [num_edges, edge_dim]
            
        Returns:
            Updated node features [num_nodes, out_channels]
        """
        return self.propagate(edge_index, x=x, edge_attr=edge_attr)
    
    def message(self, x_i: torch.Tensor, x_j: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Construct messages.
        
        Args:
            x_i: Target node features
            x_j: Source node features
            edge_attr: Edge features
            
        Returns:
            Messages
        """
        # Concatenate source, target, and edge features
        if edge_attr is not None:
            msg_input = torch.cat([x_i, x_j, edge_attr], dim=-1)
        else:
            msg_input = torch.cat([x_i, x_j], dim=-1)
        
        return self.message_net(msg_input)
    
    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """
        Update node features.
        
        Args:
            aggr_out: Aggregated messages
            x: Current node features
            
        Returns:
            Updated node features
        """
        update_input = torch.cat([x, aggr_out], dim=-1)
        return self.update_net(update_input)


class MultiScaleRiskGAT(nn.Module):
    """
    Multi-scale GAT for capturing risk at different network scales.
    """
    
    def __init__(self, node_feature_dim: int, hidden_dim: int = 128,
                 scales: list = [1, 2, 3], heads: int = 4):
        """
        Initialize multi-scale risk GAT.
        
        Args:
            node_feature_dim: Node feature dimension
            hidden_dim: Hidden dimension
            scales: List of hop distances to consider
            heads: Number of attention heads
        """
        super(MultiScaleRiskGAT, self).__init__()
        
        self.scales = scales
        self.node_encoder = nn.Linear(node_feature_dim, hidden_dim)
        
        # GAT for each scale
        self.scale_gats = nn.ModuleList([
            GATConv(hidden_dim, hidden_dim, heads=heads, concat=False)
            for _ in scales
        ])
        
        # Combine multi-scale features
        self.combiner = nn.Sequential(
            nn.Linear(hidden_dim * len(scales), hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Risk predictor
        self.risk_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with multi-scale aggregation.
        
        Args:
            x: Node features
            edge_index: Edge indices
            
        Returns:
            Risk scores
        """
        x = self.node_encoder(x)
        x = F.relu(x)
        
        # Apply GAT at each scale
        scale_features = []
        for gat in self.scale_gats:
            scale_out = gat(x, edge_index)
            scale_features.append(scale_out)
        
        # Combine scales
        combined = torch.cat(scale_features, dim=-1)
        combined = self.combiner(combined)
        
        # Predict risk
        risk_scores = self.risk_head(combined)
        risk_scores = torch.sigmoid(risk_scores)
        
        return risk_scores


if __name__ == '__main__':
    # Example usage
    num_nodes = 20
    num_edges = 50
    node_feature_dim = 16
    edge_feature_dim = 8
    
    # Create sample data
    x = torch.randn(num_nodes, node_feature_dim)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    edge_attr = torch.randn(num_edges, edge_feature_dim)
    
    # Initialize model
    model = RiskPropagationGAT(
        node_feature_dim=node_feature_dim,
        edge_feature_dim=edge_feature_dim,
        hidden_dim=64,
        output_dim=32,
        num_layers=2,
        heads=4
    )
    
    # Forward pass
    results = model(x, edge_index, edge_attr, return_attention=True)
    
    print(f"Node embeddings shape: {results['node_embeddings'].shape}")
    print(f"Risk scores shape: {results['risk_scores'].shape}")
    print(f"Systemic risk: {results['systemic_risk'].item():.4f}")
    print(f"Mean risk score: {results['risk_scores'].mean().item():.4f}")
    
    # Predict cascade
    cascade_results = model.predict_cascade(x, edge_index, edge_attr, threshold=0.6)
    print(f"\nCascade simulation:")
    print(f"  Source nodes: {len(cascade_results['source_nodes'])}")
    print(f"  Affected nodes: {cascade_results['cascade_size']}")

# Made with Bob
