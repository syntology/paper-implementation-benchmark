import numpy as np

def select_by_dist(features, selected_idx, L):
    """
    Selects L indices of samples with smallest Euclidean distance to the selected center sample.

    Parameters:
    features (array-like): Feature matrix of shape (N, D) where N is the number of samples and D is the feature dimension.
    selected_idx (int): 0-indexed index of the selected center sample.
    L (int): Number of samples to select.

    Returns:
    array: 1D integer array of shape (L,) containing the indices of the L samples with smallest Euclidean distance to the selected center sample.
    """
    features = np.asarray(features, dtype=float)
    selected_idx = int(selected_idx)
    L = int(L)

    # Compute Euclidean distances from the selected center sample to all other samples
    distances = np.linalg.norm(features - features[selected_idx], axis=1)

    # Set the distance of the selected center sample to itself to 0
    distances[selected_idx] = 0

    # Get the indices of the L samples with smallest Euclidean distance
    indices = np.argsort(distances)

    # If L > N, return all N indices sorted by distance
    if L > len(features):
        return indices

    # Otherwise, return the L indices with smallest Euclidean distance
    return indices[:L]
