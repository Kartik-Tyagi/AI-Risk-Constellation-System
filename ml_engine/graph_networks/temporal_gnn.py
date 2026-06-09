"""
Temporal Graph Neural Network
Combines graph attention with recurrent layers for time-series risk prediction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TemporalGATLayer(nn.Module):
    """
    Single layer combining GAT with temporal processing.
    """
    
    def __init__(self, in_channels: int, out_channels: int, 
                 heads: int = 4, dropout: float = 0.3):
        """
        Initialize temporal GAT layer.
        
        Args:
            in_channels: Input feature dimension
            out_channels: Output feature dimension
            heads: Number of attention heads
            dropout: Dropout probability
        """
        super(TemporalGATLayer, self).__init__()
        
        self.gat = GATConv(
            in_channels, 
            out_channels, 
            heads=heads,
            dropout=dropout,
            concat=True
        )
        
        self.lstm = nn.LSTM(
            out_channels * heads,
            out_channels * heads,
            batch_first=True
        )
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(out_channels * heads)
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            hidden_state: LSTM hidden state (h, c)
            
        Returns:
            Tuple of (output, new_hidden_state)
        """
        # Graph attention
        x = self.gat(x, edge_index)
        x = F.elu(x)
        x = self.dropout(x)
        
        # Temporal processing with LSTM
        # Reshape for LSTM: [num_nodes, 1, features]
        x = x.unsqueeze(1)
        
        if hidden_state is not None:
            x, new_hidden_state = self.lstm(x, hidden_state)
        else:
            x, new_hidden_state = self.lstm(x)
        
        # Remove time dimension: [num_nodes, features]
        x = x.squeeze(1)
        x = self.layer_norm(x)
        
        return x, new_hidden_state


class TemporalGNN(nn.Module):
    """
    Temporal Graph Neural Network for time-series risk prediction.
    Combines GAT layers with LSTM for temporal modeling.
    """
    
    def __init__(self, node_feature_dim: int, edge_feature_dim: int,
                 hidden_dim: int = 128, output_dim: int = 64,
                 num_layers: int = 3, heads: int = 4,
                 dropout: float = 0.3, prediction_horizon: int = 5):
        """
        Initialize Temporal GNN.
        
        Args:
            node_feature_dim: Dimension of node features
            edge_feature_dim: Dimension of edge features
            hidden_dim: Hidden layer dimension
            output_dim: Output dimension
            num_layers: Number of temporal GAT layers
            heads: Number of attention heads
            dropout: Dropout probability
            prediction_horizon: Number of time steps to predict ahead
        """
        super(TemporalGNN, self).__init__()
        
        self.node_feature_dim = node_feature_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.prediction_horizon = prediction_horizon
        
        # Input projection
        self.input_proj = nn.Linear(node_feature_dim, hidden_dim)
        
        # Temporal GAT layers
        self.temporal_layers = nn.ModuleList()
        for i in range(num_layers):
            if i == 0:
                in_dim = hidden_dim
            else:
                in_dim = hidden_dim * heads
            
            self.temporal_layers.append(
                TemporalGATLayer(in_dim, hidden_dim, heads, dropout)
            )
        
        # Output layers
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim * heads, hidden_dim),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # Prediction head for multi-step forecasting
        self.prediction_head = nn.Linear(output_dim, prediction_horizon)
        
        logger.info(f"Initialized TemporalGNN with {num_layers} layers, {heads} heads")
    
    def forward(self, x_sequence: List[torch.Tensor],
                edge_index_sequence: List[torch.Tensor],
                hidden_states: Optional[List[Optional[Tuple[torch.Tensor, torch.Tensor]]]] = None) -> Tuple[torch.Tensor, List[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass through temporal sequence.
        
        Args:
            x_sequence: List of node feature tensors over time
            edge_index_sequence: List of edge indices over time
            hidden_states: List of LSTM hidden states for each layer
            
        Returns:
            Tuple of (predictions, new_hidden_states)
        """
        if hidden_states is None:
            hidden_states_list: List[Optional[Tuple[torch.Tensor, torch.Tensor]]] = [None] * self.num_layers
        else:
            hidden_states_list = hidden_states
        
        new_hidden_states: List[Tuple[torch.Tensor, torch.Tensor]] = []
        
        # Process each time step
        outputs = []
        for t, (x, edge_index) in enumerate(zip(x_sequence, edge_index_sequence)):
            # Input projection
            x = self.input_proj(x)
            x = F.elu(x)
            
            # Pass through temporal layers
            layer_hidden_states: List[Tuple[torch.Tensor, torch.Tensor]] = []
            for layer_idx, layer in enumerate(self.temporal_layers):
                x, h = layer(x, edge_index, hidden_states_list[layer_idx])
                layer_hidden_states.append(h)
            
            # Update hidden states (only keep last time step's states)
            if t == len(x_sequence) - 1:
                new_hidden_states = layer_hidden_states
            
            # Output projection
            x = self.output_proj(x)
            outputs.append(x)
        
        # Stack outputs: [time_steps, num_nodes, output_dim]
        outputs = torch.stack(outputs, dim=0)
        
        # Use last time step for prediction
        last_output = outputs[-1]  # [num_nodes, output_dim]
        
        # Multi-step prediction
        predictions = self.prediction_head(last_output)  # [num_nodes, prediction_horizon]
        
        return predictions, new_hidden_states
    
    def predict_future(self, x_sequence: List[torch.Tensor],
                      edge_index_sequence: List[torch.Tensor],
                      num_future_steps: int = 5) -> torch.Tensor:
        """
        Predict future risk states.
        
        Args:
            x_sequence: Historical node features
            edge_index_sequence: Historical edge indices
            num_future_steps: Number of steps to predict
            
        Returns:
            Future predictions [num_nodes, num_future_steps]
        """
        self.eval()
        with torch.no_grad():
            predictions, _ = self.forward(x_sequence, edge_index_sequence)
            
            # Return predictions up to requested horizon
            if num_future_steps <= self.prediction_horizon:
                return predictions[:, :num_future_steps]
            else:
                # For longer horizons, use autoregressive prediction
                return self._autoregressive_predict(
                    x_sequence, edge_index_sequence, num_future_steps
                )
    
    def _autoregressive_predict(self, x_sequence: List[torch.Tensor],
                                edge_index_sequence: List[torch.Tensor],
                                num_steps: int) -> torch.Tensor:
        """
        Autoregressive multi-step prediction.
        
        Args:
            x_sequence: Historical features
            edge_index_sequence: Historical edges
            num_steps: Number of steps to predict
            
        Returns:
            Predictions [num_nodes, num_steps]
        """
        all_predictions = []
        current_sequence = x_sequence.copy()
        current_edges = edge_index_sequence.copy()
        hidden_states_opt: Optional[List[Optional[Tuple[torch.Tensor, torch.Tensor]]]] = None
        
        for step in range(num_steps):
            # Predict next step
            predictions, new_hidden_states = self.forward(
                current_sequence, current_edges, hidden_states_opt
            )
            # Cast to match expected type
            hidden_states_opt = [h for h in new_hidden_states]
            
            # Take first prediction (next time step)
            next_pred = predictions[:, 0:1]  # [num_nodes, 1]
            all_predictions.append(next_pred)
            
            # Update sequence (sliding window)
            # Use prediction as next input
            current_sequence = current_sequence[1:] + [next_pred.squeeze(1)]
            current_edges = current_edges[1:] + [current_edges[-1]]
        
        # Stack predictions
        return torch.cat(all_predictions, dim=1)


class TemporalGRUGNN(nn.Module):
    """
    Temporal GNN using GRU instead of LSTM.
    Often faster and works well for shorter sequences.
    """
    
    def __init__(self, node_feature_dim: int, hidden_dim: int = 128,
                 output_dim: int = 64, num_layers: int = 2,
                 heads: int = 4, dropout: float = 0.3):
        """
        Initialize Temporal GRU-GNN.
        
        Args:
            node_feature_dim: Node feature dimension
            hidden_dim: Hidden dimension
            output_dim: Output dimension
            num_layers: Number of layers
            heads: Number of attention heads
            dropout: Dropout probability
        """
        super(TemporalGRUGNN, self).__init__()
        
        self.input_proj = nn.Linear(node_feature_dim, hidden_dim)
        
        # GAT layers
        self.gat_layers = nn.ModuleList()
        for i in range(num_layers):
            in_dim = hidden_dim if i == 0 else hidden_dim * heads
            self.gat_layers.append(
                GATConv(in_dim, hidden_dim, heads=heads, dropout=dropout, concat=True)
            )
        
        # GRU for temporal modeling
        self.gru = nn.GRU(
            hidden_dim * heads,
            hidden_dim * heads,
            num_layers=2,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim * heads, hidden_dim),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x_sequence: List[torch.Tensor],
                edge_index_sequence: List[torch.Tensor]) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x_sequence: List of node features over time
            edge_index_sequence: List of edge indices over time
            
        Returns:
            Output predictions [num_nodes, output_dim]
        """
        temporal_embeddings = []
        
        # Process each time step through GAT
        for x, edge_index in zip(x_sequence, edge_index_sequence):
            x = self.input_proj(x)
            
            for gat_layer in self.gat_layers:
                x = gat_layer(x, edge_index)
                x = F.elu(x)
                x = self.dropout(x)
            
            temporal_embeddings.append(x)
        
        # Stack for GRU: [num_nodes, time_steps, features]
        temporal_embeddings = torch.stack(temporal_embeddings, dim=1)
        
        # GRU processing
        gru_out, _ = self.gru(temporal_embeddings)
        
        # Use last time step
        last_output = gru_out[:, -1, :]
        
        # Output projection
        output = self.output_proj(last_output)
        
        return output


class AttentionTemporalAggregator(nn.Module):
    """
    Attention-based temporal aggregation.
    Learns to weight different time steps based on importance.
    """
    
    def __init__(self, feature_dim: int):
        """
        Initialize attention aggregator.
        
        Args:
            feature_dim: Feature dimension
        """
        super(AttentionTemporalAggregator, self).__init__()
        
        self.attention = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.Tanh(),
            nn.Linear(feature_dim // 2, 1)
        )
    
    def forward(self, temporal_features: torch.Tensor) -> torch.Tensor:
        """
        Aggregate temporal features with attention.
        
        Args:
            temporal_features: [num_nodes, time_steps, features]
            
        Returns:
            Aggregated features [num_nodes, features]
        """
        # Compute attention weights
        attention_scores = self.attention(temporal_features)  # [num_nodes, time_steps, 1]
        attention_weights = F.softmax(attention_scores, dim=1)
        
        # Weighted sum
        aggregated = torch.sum(temporal_features * attention_weights, dim=1)
        
        return aggregated


if __name__ == '__main__':
    # Example usage
    print("Temporal GNN Module")
    
    # Create dummy temporal data
    num_nodes = 50
    num_time_steps = 10
    node_feature_dim = 20
    
    x_sequence = [torch.randn(num_nodes, node_feature_dim) for _ in range(num_time_steps)]
    edge_index_sequence = [torch.randint(0, num_nodes, (2, 100)) for _ in range(num_time_steps)]
    
    # Create model
    model = TemporalGNN(
        node_feature_dim=node_feature_dim,
        edge_feature_dim=5,
        hidden_dim=64,
        output_dim=32,
        num_layers=2,
        heads=4,
        prediction_horizon=5
    )
    
    # Forward pass
    predictions, hidden_states = model(x_sequence, edge_index_sequence)
    
    print(f"Input sequence length: {len(x_sequence)}")
    print(f"Predictions shape: {predictions.shape}")
    print(f"Number of hidden states: {len(hidden_states)}")

# Made with Bob
