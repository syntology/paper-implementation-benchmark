import numpy as np


def priorgrad_loss(epsilon, epsilon_theta, sigma):
    """
    Compute the PriorGrad weighted loss ||epsilon - epsilon_theta||^2_{Sigma^{-1}}.
    
    Args:
        epsilon: Sampled noise array of shape (D,)
        epsilon_theta: Model prediction array of shape (D,)
        sigma: Diagonal covariance matrix represented as 1D array of shape (D,)
               containing the diagonal elements (all positive)
    
    Returns:
        Scalar float representing the loss value
    """
    # Convert inputs to numpy arrays with float dtype
    epsilon = np.asarray(epsilon, dtype=float)
    epsilon_theta = np.asarray(epsilon_theta, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    
    # Compute the difference
    diff = epsilon - epsilon_theta
    
    # Compute the weighted squared norm: sum((diff[i]^2) / sigma[i])
    # This corresponds to ||diff||^2_{Sigma^{-1}} where Sigma is diagonal
    weighted_squared_norm = np.sum((diff ** 2) / sigma)
    
    # Return as plain Python float
    return float(weighted_squared_norm)
