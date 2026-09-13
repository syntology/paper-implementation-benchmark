import numpy as np


def compute_bootstrap_deviation(v_resampled, v_subset):
    """
    Compute the bootstrap deviation epsilon for a single bootstrap iteration
    in the Bootstrapping FQE algorithm.
    
    This implements step 8 of Algorithm (Subsampled Bootstrapping FQE):
    epsilon^(b) = hat{v}_pi(D_{K,s}^{(b)*}) - hat{v}_pi(D^{(b)}_{K,s})
    
    Args:
        v_resampled: Scalar value estimate computed on the resampled dataset
                     (hat{v}_pi(D_{K,s}^{(b)*}))
        v_subset: Scalar value estimate computed on the original subset
                  (hat{v}_pi(D^{(b)}_{K,s}))
    
    Returns:
        epsilon: Bootstrap deviation as a plain Python float
    """
    # Convert inputs to numpy arrays with float dtype
    v_resampled = np.asarray(v_resampled, dtype=float)
    v_subset = np.asarray(v_subset, dtype=float)
    
    # Compute the bootstrap deviation
    epsilon = v_resampled - v_subset
    
    # Return as plain Python float
    return float(epsilon)
