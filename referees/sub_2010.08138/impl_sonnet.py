import numpy as np


def compute_diversity_loss(x, x_prime, t, t_prime):
    """
    Compute the diversity loss for input-aware dynamic backdoor attack.
    
    L_div = ||x - x'|| / ||t - t'||
    
    where ||.|| is the Euclidean (L2) norm computed by flattening the array
    and taking sqrt(sum of squares).
    
    Args:
        x: Input image (numpy array)
        x_prime: Another input image (numpy array, same shape as x)
        t: Trigger pattern for x (numpy array, same shape as x)
        t_prime: Trigger pattern for x_prime (numpy array, same shape as x)
    
    Returns:
        float: The diversity loss value. Returns inf if denominator is zero.
    """
    # Convert inputs to numpy arrays with float dtype
    x = np.asarray(x, dtype=float)
    x_prime = np.asarray(x_prime, dtype=float)
    t = np.asarray(t, dtype=float)
    t_prime = np.asarray(t_prime, dtype=float)
    
    # Compute numerator: ||x - x'||
    x_diff = x - x_prime
    x_diff_flat = x_diff.flatten()
    numerator = np.sqrt(np.sum(x_diff_flat ** 2))
    
    # Compute denominator: ||t - t'||
    t_diff = t - t_prime
    t_diff_flat = t_diff.flatten()
    denominator = np.sqrt(np.sum(t_diff_flat ** 2))
    
    # Handle division by zero
    if denominator == 0.0:
        return float(np.inf)
    
    # Compute and return diversity loss
    result = numerator / denominator
    return float(result)
