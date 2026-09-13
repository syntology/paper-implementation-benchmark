import numpy as np

def compute_euclidean_norm(array):
    """
    Compute the Euclidean (L2) norm of a numpy array.
    
    Parameters:
    array (numpy array): Input array.
    
    Returns:
    float: Euclidean norm of the input array.
    """
    return np.sqrt(np.sum(array ** 2))

def compute_diversity_loss(x, x_prime, t, t_prime):
    """
    Compute the diversity loss L_div = ||x - x'|| / ||t - t'||.
    
    Parameters:
    x (numpy array): Input image.
    x_prime (numpy array): Another input image.
    t (numpy array): Trigger pattern.
    t_prime (numpy array): Another trigger pattern.
    
    Returns:
    float: Diversity loss.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    x = np.asarray(x, dtype=float)
    x_prime = np.asarray(x_prime, dtype=float)
    t = np.asarray(t, dtype=float)
    t_prime = np.asarray(t_prime, dtype=float)
    
    # Compute the numerator and denominator of the diversity loss
    numerator = compute_euclidean_norm(x - x_prime)
    denominator = compute_euclidean_norm(t - t_prime)
    
    # Check for division by zero
    if denominator == 0:
        return np.inf
    
    # Compute and return the diversity loss
    return numerator / denominator
