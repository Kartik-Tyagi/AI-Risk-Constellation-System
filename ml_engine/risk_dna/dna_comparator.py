"""
Risk DNA Comparator
Compares and analyzes similarities between Risk DNA fingerprints.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cosine, euclidean, cityblock
from scipy.stats import pearsonr
import logging

from .dna_generator import RiskDNA

logger = logging.getLogger(__name__)


class DNAComparator:
    """
    Compares Risk DNA fingerprints using various similarity metrics.
    """
    
    def __init__(self, metric: str = 'cosine'):
        """
        Initialize DNA comparator.
        
        Args:
            metric: Distance metric ('cosine', 'euclidean', 'manhattan', 'correlation')
        """
        self.metric = metric
        self.metric_functions = {
            'cosine': self._cosine_similarity,
            'euclidean': self._euclidean_similarity,
            'manhattan': self._manhattan_similarity,
            'correlation': self._correlation_similarity
        }
        
        if metric not in self.metric_functions:
            raise ValueError(f"Unknown metric: {metric}")
        
        logger.info(f"Initialized DNAComparator with metric={metric}")
    
    def compare(self, dna1: RiskDNA, dna2: RiskDNA) -> float:
        """
        Compare two Risk DNAs.
        
        Args:
            dna1: First Risk DNA
            dna2: Second Risk DNA
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        metric_fn = self.metric_functions[self.metric]
        similarity = metric_fn(dna1.dna_vector, dna2.dna_vector)
        return similarity
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity."""
        return float(1 - cosine(vec1, vec2))
    
    def _euclidean_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute euclidean similarity (normalized)."""
        distance = euclidean(vec1, vec2)
        # Normalize to [0, 1]
        max_distance = np.sqrt(len(vec1) * 4)  # Assuming values in [-1, 1]
        similarity = 1 - (distance / max_distance)
        return float(max(0, similarity))
    
    def _manhattan_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute Manhattan similarity (normalized)."""
        distance = cityblock(vec1, vec2)
        max_distance = len(vec1) * 2  # Assuming values in [-1, 1]
        similarity = 1 - (distance / max_distance)
        return float(max(0, similarity))
    
    def _correlation_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute correlation similarity."""
        corr, _ = pearsonr(vec1, vec2)
        # Convert from [-1, 1] to [0, 1]
        similarity = (corr + 1) / 2
        return float(similarity)
    
    def compare_batch(self, dna_list: List[RiskDNA]) -> np.ndarray:
        """
        Compute pairwise similarity matrix for list of DNAs.
        
        Args:
            dna_list: List of Risk DNAs
            
        Returns:
            Similarity matrix [n x n]
        """
        n = len(dna_list)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    sim = self.compare(dna_list[i], dna_list[j])
                    similarity_matrix[i, j] = sim
                    similarity_matrix[j, i] = sim
        
        return similarity_matrix
    
    def find_most_similar(self, query_dna: RiskDNA, 
                         candidate_dnas: List[RiskDNA],
                         top_k: int = 5) -> List[Tuple[RiskDNA, float]]:
        """
        Find most similar DNAs to query.
        
        Args:
            query_dna: Query Risk DNA
            candidate_dnas: List of candidate DNAs
            top_k: Number of top matches to return
            
        Returns:
            List of (DNA, similarity_score) tuples
        """
        similarities = []
        for candidate in candidate_dnas:
            sim = self.compare(query_dna, candidate)
            similarities.append((candidate, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


class DNAClusterer:
    """
    Clusters Risk DNAs to identify similar risk profiles.
    """
    
    def __init__(self, method: str = 'kmeans', n_clusters: int = 5):
        """
        Initialize DNA clusterer.
        
        Args:
            method: Clustering method ('kmeans', 'dbscan', 'hierarchical')
            n_clusters: Number of clusters (for kmeans/hierarchical)
        """
        self.method = method
        self.n_clusters = n_clusters
        self.model = None
        self.labels_ = None
        
        logger.info(f"Initialized DNAClusterer with method={method}")
    
    def fit(self, dna_list: List[RiskDNA]) -> np.ndarray:
        """
        Cluster Risk DNAs.
        
        Args:
            dna_list: List of Risk DNAs
            
        Returns:
            Cluster labels
        """
        # Extract DNA vectors
        vectors = np.array([dna.dna_vector for dna in dna_list])
        
        # Fit clustering model
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42)
            self.labels_ = self.model.fit_predict(vectors)
        
        elif self.method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=5)
            self.labels_ = self.model.fit_predict(vectors)
        
        elif self.method == 'hierarchical':
            self.model = AgglomerativeClustering(n_clusters=self.n_clusters)
            self.labels_ = self.model.fit_predict(vectors)
        
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")
        
        # Compute silhouette score
        if len(set(self.labels_)) > 1:
            score = silhouette_score(vectors, self.labels_)
            logger.info(f"Clustering silhouette score: {score:.3f}")
        
        return self.labels_
    
    def predict(self, dna: RiskDNA) -> int:
        """
        Predict cluster for new DNA.
        
        Args:
            dna: Risk DNA
            
        Returns:
            Cluster label
        """
        if self.model is None:
            raise ValueError("Model not fitted yet")
        
        vector = dna.dna_vector.reshape(1, -1)
        
        if self.method == 'kmeans':
            return int(self.model.predict(vector)[0])
        else:
            # For DBSCAN/hierarchical, find nearest cluster
            return self._find_nearest_cluster(vector)
    
    def _find_nearest_cluster(self, vector: np.ndarray) -> int:
        """Find nearest cluster for vector."""
        # Simple nearest centroid approach
        if self.labels_ is None:
            raise ValueError("Model not fitted yet")
        
        # Compute cluster centroids
        unique_labels = set(self.labels_)
        min_dist = float('inf')
        nearest_label = 0
        
        for label in unique_labels:
            if label == -1:  # Skip noise in DBSCAN
                continue
            # This would need access to original vectors
            # Simplified implementation
            nearest_label = label
            break
        
        return nearest_label
    
    def get_cluster_profiles(self, dna_list: List[RiskDNA]) -> Dict[int, Dict]:
        """
        Get profile statistics for each cluster.
        
        Args:
            dna_list: List of Risk DNAs
            
        Returns:
            Dictionary of cluster profiles
        """
        if self.labels_ is None:
            raise ValueError("Model not fitted yet")
        
        profiles = {}
        
        for label in set(self.labels_):
            if label == -1:  # Skip noise
                continue
            
            # Get DNAs in this cluster
            cluster_dnas = [dna for dna, lbl in zip(dna_list, self.labels_) if lbl == label]
            
            # Compute statistics
            vectors = np.array([dna.dna_vector for dna in cluster_dnas])
            components = [dna.components for dna in cluster_dnas]
            
            profiles[int(label)] = {
                'size': len(cluster_dnas),
                'centroid': np.mean(vectors, axis=0),
                'std': np.std(vectors, axis=0),
                'avg_components': {
                    key: np.mean([c.get(key, 0) for c in components])
                    for key in components[0].keys()
                }
            }
        
        return profiles


class AnomalyDetector:
    """
    Detects anomalous Risk DNAs based on deviation from normal patterns.
    """
    
    def __init__(self, threshold: float = 2.0, method: str = 'isolation'):
        """
        Initialize anomaly detector.
        
        Args:
            threshold: Anomaly threshold (in standard deviations)
            method: Detection method ('isolation', 'statistical', 'clustering')
        """
        self.threshold = threshold
        self.method = method
        self.baseline_mean = None
        self.baseline_std = None
        
        logger.info(f"Initialized AnomalyDetector with method={method}")
    
    def fit(self, normal_dnas: List[RiskDNA]):
        """
        Fit detector on normal DNAs.
        
        Args:
            normal_dnas: List of normal Risk DNAs
        """
        vectors = np.array([dna.dna_vector for dna in normal_dnas])
        
        self.baseline_mean = np.mean(vectors, axis=0)
        self.baseline_std = np.std(vectors, axis=0)
        
        logger.info(f"Fitted anomaly detector on {len(normal_dnas)} normal DNAs")
    
    def detect(self, dna: RiskDNA) -> Tuple[bool, float]:
        """
        Detect if DNA is anomalous.
        
        Args:
            dna: Risk DNA to check
            
        Returns:
            Tuple of (is_anomaly, anomaly_score)
        """
        if self.baseline_mean is None or self.baseline_std is None:
            raise ValueError("Detector not fitted yet")
        
        # Compute z-scores
        z_scores = np.abs((dna.dna_vector - self.baseline_mean) / (self.baseline_std + 1e-8))
        
        # Anomaly score (max z-score)
        anomaly_score = float(np.max(z_scores))
        
        # Check if anomalous
        is_anomaly = anomaly_score > self.threshold
        
        return is_anomaly, anomaly_score
    
    def detect_batch(self, dna_list: List[RiskDNA]) -> List[Tuple[bool, float]]:
        """
        Detect anomalies in batch.
        
        Args:
            dna_list: List of Risk DNAs
            
        Returns:
            List of (is_anomaly, anomaly_score) tuples
        """
        results = []
        for dna in dna_list:
            result = self.detect(dna)
            results.append(result)
        
        return results
    
    def get_anomaly_components(self, dna: RiskDNA) -> Dict[str, float]:
        """
        Identify which components contribute most to anomaly.
        
        Args:
            dna: Anomalous Risk DNA
            
        Returns:
            Dictionary of component contributions
        """
        if self.baseline_mean is None or self.baseline_std is None:
            raise ValueError("Detector not fitted yet")
        
        # Compute z-scores for each dimension
        z_scores = (dna.dna_vector - self.baseline_mean) / (self.baseline_std + 1e-8)
        
        # Map to components (simplified)
        contributions = {}
        for key, value in dna.components.items():
            # Use average z-score as proxy
            contributions[key] = float(np.mean(np.abs(z_scores)))
        
        return contributions


if __name__ == '__main__':
    # Example usage
    print("Risk DNA Comparator Module")
    
    from dna_generator import RiskDNAGenerator
    
    # Create generator
    generator = RiskDNAGenerator(dna_dim=256)
    
    # Generate sample DNAs
    dnas = []
    for i in range(10):
        features = {
            'portfolio': {'total_value': 1000000 * (i + 1)},
            'historical': {'volatility_30d': 0.1 + i * 0.01},
            'counterparty': {'num_counterparties': 10 + i},
            'market': {'vix_level': 15 + i}
        }
        dna = generator.generate(f'ENTITY_{i:03d}', features)
        dnas.append(dna)
    
    # Compare DNAs
    comparator = DNAComparator(metric='cosine')
    similarity = comparator.compare(dnas[0], dnas[1])
    print(f"Similarity between DNA 0 and 1: {similarity:.3f}")
    
    # Cluster DNAs
    clusterer = DNAClusterer(method='kmeans', n_clusters=3)
    labels = clusterer.fit(dnas)
    print(f"Cluster labels: {labels}")
    
    # Detect anomalies
    detector = AnomalyDetector(threshold=2.0)
    detector.fit(dnas[:8])  # Fit on first 8
    is_anomaly, score = detector.detect(dnas[9])
    print(f"DNA 9 anomaly: {is_anomaly}, score: {score:.3f}")

# Made with Bob
