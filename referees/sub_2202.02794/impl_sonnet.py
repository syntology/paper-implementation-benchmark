import numpy as np


def compute_typicality(embeddings, cluster_assignments, point_index):
    """
    Compute the typicality score for a single point within its assigned cluster.
    
    Typicality is defined as the negative Euclidean distance from the point to
    the centroid of its assigned cluster. Higher (less negative) values indicate
    more typical points closer to the cluster center.
    
    Args:
        embeddings: (N, D) array of embeddings where N is the number of points
                    and D is the embedding dimension
        cluster_assignments: length-N array of integer cluster labels (0-indexed)
        point_index: scalar 0-indexed integer in range [0, N-1]
    
    Returns:
        float: typicality score (negative Euclidean distance to cluster centroid)
    """
    # Convert inputs to numpy arrays
    embeddings = np.asarray(embeddings, dtype=float)
    cluster_assignments = np.asarray(cluster_assignments, dtype=float)
    
    # Step 1: Identify the cluster label for the point
    c = cluster_assignments[point_index]
    
    # Step 2: Find all points in cluster c
    mask = (cluster_assignments == c)
    
    # Step 3: Compute the centroid of cluster c
    cluster_points = embeddings[mask]
    centroid = np.mean(cluster_points, axis=0)
    
    # Step 4: Compute the Euclidean distance from the point to the centroid
    point = embeddings[point_index]
    diff = point - centroid
    d = np.sqrt(np.sum(diff ** 2))
    
    # Step 5: Return negative distance
    return float(-d)
