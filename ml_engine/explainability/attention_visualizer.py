"""
Attention Visualizer
Visualizes GAT (Graph Attention Network) attention weights
"""

import numpy as np
import torch
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AttentionVisualizer:
    """Visualize attention weights from Graph Attention Networks"""
    
    def __init__(self, gat_model):
        """
        Initialize attention visualizer
        
        Args:
            gat_model: Trained GAT model with attention mechanisms
        """
        self.model = gat_model
        self.attention_weights = {}
        
    def extract_attention_weights(
        self,
        graph_data: Dict[str, Any],
        layer_idx: int = -1
    ) -> Dict[str, Any]:
        """
        Extract attention weights from GAT model
        
        Args:
            graph_data: Graph data (nodes, edges, features)
            layer_idx: Layer index (-1 for last layer)
            
        Returns:
            Dictionary containing attention weights
        """
        try:
            # Set model to evaluation mode
            self.model.eval()
            
            # Prepare input
            node_features = torch.tensor(graph_data['node_features'], dtype=torch.float32)
            edge_index = torch.tensor(graph_data['edge_index'], dtype=torch.long)
            
            # Forward pass with attention extraction
            with torch.no_grad():
                output, attention_weights = self.model.forward_with_attention(
                    node_features,
                    edge_index
                )
            
            # Get attention for specified layer
            if isinstance(attention_weights, list):
                attn = attention_weights[layer_idx]
            else:
                attn = attention_weights
            
            # Convert to numpy
            attn_np = attn.cpu().numpy()
            
            # Create attention map
            attention_map = self._create_attention_map(
                attn_np,
                edge_index.cpu().numpy(),
                graph_data.get('node_ids', [])
            )
            
            return {
                'attention_weights': attn_np.tolist(),
                'attention_map': attention_map,
                'layer_index': layer_idx,
                'num_nodes': len(node_features),
                'num_edges': edge_index.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Error extracting attention weights: {e}")
            return {'error': str(e)}
    
    def _create_attention_map(
        self,
        attention_weights: np.ndarray,
        edge_index: np.ndarray,
        node_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Create attention map from weights and edges
        
        Args:
            attention_weights: Attention weight matrix
            edge_index: Edge connectivity (2, num_edges)
            node_ids: List of node identifiers
            
        Returns:
            List of attention edges
        """
        attention_map = []
        
        for i in range(edge_index.shape[1]):
            source_idx = int(edge_index[0, i])
            target_idx = int(edge_index[1, i])
            
            # Get attention weight for this edge
            if i < len(attention_weights):
                weight = float(attention_weights[i])
            else:
                weight = 0.0
            
            # Get node IDs
            source_id = node_ids[source_idx] if source_idx < len(node_ids) else f"node_{source_idx}"
            target_id = node_ids[target_idx] if target_idx < len(node_ids) else f"node_{target_idx}"
            
            attention_map.append({
                'source': source_id,
                'target': target_id,
                'source_idx': source_idx,
                'target_idx': target_idx,
                'attention': weight,
                'normalized_attention': weight  # Already normalized by softmax
            })
        
        # Sort by attention weight
        attention_map.sort(key=lambda x: x['attention'], reverse=True)
        
        return attention_map
    
    def get_top_attention_edges(
        self,
        graph_data: Dict[str, Any],
        top_k: int = 10,
        layer_idx: int = -1
    ) -> List[Dict[str, Any]]:
        """
        Get top-k edges by attention weight
        
        Args:
            graph_data: Graph data
            top_k: Number of top edges to return
            layer_idx: Layer index
            
        Returns:
            List of top attention edges
        """
        attention_data = self.extract_attention_weights(graph_data, layer_idx)
        
        if 'error' in attention_data:
            return []
        
        return attention_data['attention_map'][:top_k]
    
    def get_node_attention_summary(
        self,
        graph_data: Dict[str, Any],
        node_id: str,
        layer_idx: int = -1
    ) -> Dict[str, Any]:
        """
        Get attention summary for a specific node
        
        Args:
            graph_data: Graph data
            node_id: Node identifier
            layer_idx: Layer index
            
        Returns:
            Node attention summary
        """
        attention_data = self.extract_attention_weights(graph_data, layer_idx)
        
        if 'error' in attention_data:
            return attention_data
        
        attention_map = attention_data['attention_map']
        
        # Find edges involving this node
        incoming_attention = []
        outgoing_attention = []
        
        for edge in attention_map:
            if edge['target'] == node_id:
                incoming_attention.append(edge)
            if edge['source'] == node_id:
                outgoing_attention.append(edge)
        
        # Calculate statistics
        incoming_weights = [e['attention'] for e in incoming_attention]
        outgoing_weights = [e['attention'] for e in outgoing_attention]
        
        return {
            'node_id': node_id,
            'incoming_attention': incoming_attention,
            'outgoing_attention': outgoing_attention,
            'incoming_stats': {
                'count': len(incoming_weights),
                'mean': float(np.mean(incoming_weights)) if incoming_weights else 0.0,
                'max': float(np.max(incoming_weights)) if incoming_weights else 0.0,
                'total': float(np.sum(incoming_weights)) if incoming_weights else 0.0
            },
            'outgoing_stats': {
                'count': len(outgoing_weights),
                'mean': float(np.mean(outgoing_weights)) if outgoing_weights else 0.0,
                'max': float(np.max(outgoing_weights)) if outgoing_weights else 0.0,
                'total': float(np.sum(outgoing_weights)) if outgoing_weights else 0.0
            }
        }
    
    def visualize_attention_flow(
        self,
        graph_data: Dict[str, Any],
        source_node: str,
        max_depth: int = 3,
        layer_idx: int = -1
    ) -> Dict[str, Any]:
        """
        Visualize attention flow from a source node
        
        Args:
            graph_data: Graph data
            source_node: Source node identifier
            max_depth: Maximum propagation depth
            layer_idx: Layer index
            
        Returns:
            Attention flow visualization data
        """
        attention_data = self.extract_attention_weights(graph_data, layer_idx)
        
        if 'error' in attention_data:
            return attention_data
        
        attention_map = attention_data['attention_map']
        
        # Build adjacency list
        adjacency = {}
        for edge in attention_map:
            source = edge['source']
            target = edge['target']
            weight = edge['attention']
            
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append({'target': target, 'weight': weight})
        
        # BFS to find attention flow
        visited = set()
        flow_paths = []
        queue = [(source_node, 0, 1.0, [source_node])]
        
        while queue:
            current, depth, cumulative_weight, path = queue.pop(0)
            
            if depth >= max_depth or current in visited:
                continue
            
            visited.add(current)
            
            if current in adjacency:
                for neighbor in adjacency[current]:
                    target = neighbor['target']
                    weight = neighbor['weight']
                    new_weight = cumulative_weight * weight
                    new_path = path + [target]
                    
                    flow_paths.append({
                        'path': new_path,
                        'depth': depth + 1,
                        'cumulative_weight': new_weight,
                        'final_node': target
                    })
                    
                    queue.append((target, depth + 1, new_weight, new_path))
        
        # Sort by cumulative weight
        flow_paths.sort(key=lambda x: x['cumulative_weight'], reverse=True)
        
        return {
            'source_node': source_node,
            'max_depth': max_depth,
            'flow_paths': flow_paths[:20],  # Top 20 paths
            'total_paths': len(flow_paths)
        }
    
    def export_attention_matrix(
        self,
        graph_data: Dict[str, Any],
        layer_idx: int = -1
    ) -> np.ndarray:
        """
        Export attention as adjacency matrix
        
        Args:
            graph_data: Graph data
            layer_idx: Layer index
            
        Returns:
            Attention adjacency matrix
        """
        attention_data = self.extract_attention_weights(graph_data, layer_idx)
        
        if 'error' in attention_data:
            return np.array([])
        
        num_nodes = attention_data['num_nodes']
        attention_map = attention_data['attention_map']
        
        # Create adjacency matrix
        matrix = np.zeros((num_nodes, num_nodes))
        
        for edge in attention_map:
            source_idx = edge['source_idx']
            target_idx = edge['target_idx']
            weight = edge['attention']
            matrix[source_idx, target_idx] = weight
        
        return matrix
    
    def compare_attention_layers(
        self,
        graph_data: Dict[str, Any],
        layer_indices: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Compare attention across multiple layers
        
        Args:
            graph_data: Graph data
            layer_indices: List of layer indices to compare
            
        Returns:
            Layer comparison data
        """
        if layer_indices is None:
            # Compare all layers
            layer_indices = list(range(len(self.model.gat_layers)))
        
        layer_comparisons = []
        
        for layer_idx in layer_indices:
            attention_data = self.extract_attention_weights(graph_data, layer_idx)
            
            if 'error' not in attention_data:
                attention_weights = attention_data['attention_weights']
                
                layer_comparisons.append({
                    'layer_index': layer_idx,
                    'mean_attention': float(np.mean(attention_weights)),
                    'std_attention': float(np.std(attention_weights)),
                    'max_attention': float(np.max(attention_weights)),
                    'min_attention': float(np.min(attention_weights)),
                    'sparsity': float(np.sum(np.array(attention_weights) < 0.01) / len(attention_weights))
                })
        
        return {
            'layer_comparisons': layer_comparisons,
            'num_layers': len(layer_comparisons)
        }


def create_attention_visualizer(gat_model) -> AttentionVisualizer:
    """
    Factory function to create attention visualizer
    
    Args:
        gat_model: Trained GAT model
        
    Returns:
        AttentionVisualizer instance
    """
    return AttentionVisualizer(gat_model)


# Made with Bob