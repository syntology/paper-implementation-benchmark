import numpy as np


def select_by_dist(features, selected_idx, L):
    """
    Select L samples closest to the selected center sample by Euclidean distance.
    
    Args:
        features: Feature matrix of shape (N, D)
        selected_idx: Index of the selected center sample (0-indexed)
        L: Number of samples to select
    
    Returns:
        1D integer array of shape (L,) containing indices of L closest samples,
        sorted in ascending order of distance (ties broken by index order).
        If L > N, returns all N indices.
    """
    features = np.asarray(features, dtype=float)
    selected_idx = int(selected_idx)
    L = int(L)
    
    N = features.shape[0]
    
    # If L >= N, return all indices sorted by distance
    if L >= N:
        L = N
    
    # Get the center feature vector
    center = features[selected_idx]
    
    # Compute Euclidean distances from all samples to the center
    # Distance: sqrt(sum((features[i] - center)**2))
    diff = features - center  # Shape: (N, D)
    distances = np.sqrt(np.sum(diff ** 2, axis=1))  # Shape: (N,)
    
    # Create array of indices
    indices = np.arange(N)
    
    # Sort by distance first, then by index (for tie-breaking)
    # We use stable sort to maintain index order for equal distances
    # First sort by index (already in order), then stable sort by distance
    sorted_indices = np.argsort(distances, kind='stable')
    
    # Select the first L indices
    result = sorted_indices[:L]
    
    # Sort result by distance (and index for ties) to ensure proper ordering
    result_distances = distances[result]
    final_sort = np.argsort(result_distances, kind='stable')
    result = result[final_sort]
    
    return result
