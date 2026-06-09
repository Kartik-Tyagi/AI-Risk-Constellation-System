"""
Graph Attention Network (GAT) Model
Multi-head attention mechanism for graph neural networks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, softmax
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GATConv(MessagePassing):
    """
    Graph Attention Convolution Layer.
    Implements multi-head attention mechanism for graph data.
    """
    
    def __init__(self, in_channels: int, out_channels: int, heads: int = 1,
                 concat: bool = True, negative_slope: float = 0.2,
                 dropout: float = 0.0, add_self_loops: bool = True,
                 bias: bool = True):
        """
        Initialize GAT convolution layer.
        
        Args:
            in_channels: Input feature dimension
            out_channels: Output feature dimension per head
            heads: Number of attention heads
            concat: If True, concatenate head outputs; else average
            negative_slope: LeakyReLU negative slope
            dropout: Dropout probability
            add_self_loops: Whether to add self-loops
            bias: Whether to use bias
        """
        super(GATConv, self).__init__(aggr='add', node_dim=0)
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.concat = concat
        self.negative_slope = negative_slope
        self.dropout = dropout
        self.add_self_loops_flag = add_self_loops
        
        # Linear transformation for input features
        self.lin = nn.Linear(in_channels, heads * out_channels, bias=False)
        
        # Attention parameters
        self.att_src = nn.Parameter(torch.Tensor(1, heads, out_channels))
        self.att_dst = nn.Parameter(torch.Tensor(1, heads, out_channels))
        
        if bias and concat:
            self.bias = nn.Parameter(torch.Tensor(heads * out_channels))
        elif bias and not concat:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """Initialize parameters."""
        nn.init.xavier_uniform_(self.lin.weight)
        nn.init.xavier_uniform_(self.att_src)
        nn.init.xavier_uniform_(self.att_dst)
        if self.bias is not None:
            nn.init.zeros_(self.bias)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None,
                return_attention_weights: bool = False):
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge features [num_edges, edge_dim]
            return_attention_weights: Whether to return attention weights
            
        Returns:
            Updated node features and optionally attention weights
        """
        # Add self-loops
        if self.add_self_loops_flag:
            edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))
        
        # Linear transformation
        x = self.lin(x).view(-1, self.heads, self.out_channels)
        
        # Propagate messages
        attention_weights = None
        out = self.propagate(edge_index, x=x, edge_attr=edge_attr,
                           return_attention_weights=return_attention_weights)
        
        if return_attention_weights:
            out, attention_weights = out
        
        # Concatenate or average heads
        if self.concat:
            out = out.view(-1, self.heads * self.out_channels)
        else:
            out = out.mean(dim=1)
        
        # Add bias
        if self.bias is not None:
            out = out + self.bias
        
        if return_attention_weights:
            return out, attention_weights
        else:
            return out
    
    def message(self, x_i: torch.Tensor, x_j: torch.Tensor,
                edge_index_i: torch.Tensor, size_i: Optional[int],
                edge_attr: Optional[torch.Tensor] = None,
                return_attention_weights: bool = False):
        """
        Compute messages and attention coefficients.
        
        Args:
            x_i: Target node features
            x_j: Source node features
            edge_index_i: Target node indices
            size_i: Number of target nodes
            edge_attr: Edge features
            return_attention_weights: Whether to return attention weights
            
        Returns:
            Messages and optionally attention weights
        """
        # Compute attention coefficients
        alpha_src = (x_j * self.att_src).sum(dim=-1)
        alpha_dst = (x_i * self.att_dst).sum(dim=-1)
        alpha = alpha_src + alpha_dst
        alpha = F.leaky_relu(alpha, self.negative_slope)
        
        # Incorporate edge features if provided
        if edge_attr is not None:
            # Simple approach: add edge features to attention
            edge_attr_tensor = edge_attr
            if edge_attr_tensor.dim() == 1:
                edge_attr_tensor = edge_attr_tensor.unsqueeze(-1)
            alpha = alpha + edge_attr_tensor.sum(dim=-1, keepdim=True)
        
        # Softmax normalization
        alpha = softmax(alpha, edge_index_i, num_nodes=size_i)
        
        # Dropout
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)
        
        # Compute messages
        out = x_j * alpha.unsqueeze(-1)
        
        if return_attention_weights:
            return out, (edge_index_i, alpha)
        else:
            return out


class GAT(nn.Module):
    """
    Multi-layer Graph Attention Network.
    """
    
    def __init__(self, in_channels: int, hidden_channels: int,
                 out_channels: int, num_layers: int = 2, heads: int = 8,
                 dropout: float = 0.6, concat_heads: bool = True):
        """
        Initialize GAT model.
        
        Args:
            in_channels: Input feature dimension
            hidden_channels: Hidden layer dimension
            out_channels: Output dimension
            num_layers: Number of GAT layers
            heads: Number of attention heads
            dropout: Dropout probability
            concat_heads: Whether to concatenate heads in hidden layers
        """
        super(GAT, self).__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        
        # First layer
        self.convs.append(
            GATConv(in_channels, hidden_channels, heads=heads,
                   concat=concat_heads, dropout=dropout)
        )
        self.norms.append(nn.LayerNorm(hidden_channels * heads if concat_heads else hidden_channels))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            in_dim = hidden_channels * heads if concat_heads else hidden_channels
            self.convs.append(
                GATConv(in_dim, hidden_channels, heads=heads,
                       concat=concat_heads, dropout=dropout)
            )
            self.norms.append(nn.LayerNorm(hidden_channels * heads if concat_heads else hidden_channels))
        
        # Output layer
        if num_layers > 1:
            in_dim = hidden_channels * heads if concat_heads else hidden_channels
            self.convs.append(
                GATConv(in_dim, out_channels, heads=1,
                       concat=False, dropout=dropout)
            )
        
        logger.info(f"Initialized GAT with {num_layers} layers, {heads} heads")
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None,
                return_attention_weights: bool = False):
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            edge_attr: Edge features [num_edges, edge_dim]
            return_attention_weights: Whether to return attention weights
            
        Returns:
            Node embeddings and optionally attention weights
        """
        attention_weights = []
        
        for i, conv in enumerate(self.convs):
            if return_attention_weights and i == len(self.convs) - 1:
                x, attn = conv(x, edge_index, edge_attr, return_attention_weights=True)
                attention_weights.append(attn)
            else:
                x = conv(x, edge_index, edge_attr)
            
            # Apply normalization and activation (except last layer)
            if i < len(self.convs) - 1:
                x = self.norms[i](x)
                x = F.elu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        
        if return_attention_weights:
            return x, attention_weights
        else:
            return x
    
    def get_attention_weights(self, x: torch.Tensor, edge_index: torch.Tensor,
                             edge_attr: Optional[torch.Tensor] = None):
        """
        Get attention weights from the last layer.
        
        Args:
            x: Node features
            edge_index: Edge indices
            edge_attr: Edge features
            
        Returns:
            Attention weights
        """
        _, attention_weights = self.forward(x, edge_index, edge_attr,
                                           return_attention_weights=True)
        return attention_weights


class MultiHeadGATLayer(nn.Module):
    """
    Multi-head GAT layer with residual connections.
    """
    
    def __init__(self, in_channels: int, out_channels: int, heads: int = 8,
                 dropout: float = 0.6, residual: bool = True):
        """
        Initialize multi-head GAT layer.
        
        Args:
            in_channels: Input dimension
            out_channels: Output dimension per head
            heads: Number of attention heads
            dropout: Dropout probability
            residual: Whether to use residual connection
        """
        super(MultiHeadGATLayer, self).__init__()
        
        self.gat = GATConv(in_channels, out_channels, heads=heads,
                          concat=True, dropout=dropout)
        self.norm = nn.LayerNorm(out_channels * heads)
        self.residual = residual
        
        if residual and in_channels != out_channels * heads:
            self.residual_proj = nn.Linear(in_channels, out_channels * heads)
        else:
            self.residual_proj = None
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None):
        """Forward pass with residual connection."""
        identity = x
        
        x = self.gat(x, edge_index, edge_attr)
        x = self.norm(x)
        
        if self.residual:
            if self.residual_proj is not None:
                identity = self.residual_proj(identity)
            x = x + identity
        
        x = F.elu(x)
        
        return x


if __name__ == '__main__':
    # Example usage
    import torch_geometric
    from torch_geometric.data import Data
    
    # Create sample graph
    num_nodes = 10
    num_features = 16
    num_edges = 30
    
    x = torch.randn(num_nodes, num_features)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Create GAT model
    model = GAT(
        in_channels=num_features,
        hidden_channels=32,
        out_channels=8,
        num_layers=3,
        heads=4,
        dropout=0.6
    )
    
    # Forward pass
    out = model(x, edge_index)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {out.shape}")
    
    # Get attention weights
    attention_weights = model.get_attention_weights(x, edge_index)
    print(f"Attention weights: {len(attention_weights)} layers")

# Made with Bob
