import numpy as np


def fragment_score(fragment_counts, fragment_properties):
    """
    Compute scores for molecular fragments according to Eq. (score).
    
    For each fragment i:
        score[i] = fragment_counts[i] * mean(fragment_properties[i, :])
    
    If a fragment has zero properties (P=0), treat mean as 1.0.
    
    Args:
        fragment_counts: 1D array of length N, occurrence count of each fragment
        fragment_properties: 2D array of shape (N, P), property values for each fragment
    
    Returns:
        1D array of length N containing the score for each fragment
    """
    # Convert inputs to numpy arrays with float dtype
    fragment_counts = np.asarray(fragment_counts, dtype=float)
    fragment_properties = np.asarray(fragment_properties, dtype=float)
    
    # Get the number of fragments
    N = len(fragment_counts)
    
    # Handle the case where fragment_properties might be 1D or empty
    if fragment_properties.ndim == 1:
        fragment_properties = fragment_properties.reshape(N, -1)
    
    # Get number of properties
    if fragment_properties.size == 0 or fragment_properties.shape[1] == 0:
        # P = 0 case: treat mean as 1.0
        property_means = np.ones(N, dtype=float)
    else:
        # Compute mean of properties for each fragment (axis=1 for row-wise mean)
        property_means = np.mean(fragment_properties, axis=1)
    
    # Compute score: count * mean(properties)
    scores = fragment_counts * property_means
    
    return scores
