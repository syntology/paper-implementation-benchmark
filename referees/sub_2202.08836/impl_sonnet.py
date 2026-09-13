import numpy as np


def compute_conformal_epsilon(nonconformity_scores, alpha):
    """
    Compute the conformal prediction threshold epsilon from calibration nonconformity scores.
    
    Args:
        nonconformity_scores: 1D array-like of shape (n,) containing non-negative floats
                            representing calibration residuals
        alpha: float in (0,1) representing the significance level
    
    Returns:
        float: threshold epsilon for conformal prediction
    """
    # Convert input to numpy array
    scores = np.asarray(nonconformity_scores, dtype=float)
    
    # Get the number of calibration samples
    n = len(scores)
    
    # Sort nonconformity scores in ascending order
    sorted_scores = np.sort(scores)
    
    # Compute the index k = ceil((n+1)*(1-alpha)) - 1
    # The -1 converts from 1-indexed position to 0-indexed array position
    k = int(np.ceil((n + 1) * (1 - alpha))) - 1
    
    # If k >= n, return the maximum value; otherwise return the k-th element
    if k >= n:
        epsilon = float(np.max(sorted_scores))
    else:
        epsilon = float(sorted_scores[k])
    
    return epsilon
