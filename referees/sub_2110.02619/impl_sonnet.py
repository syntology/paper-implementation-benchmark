import numpy as np


def update_alpha_weights(alpha_current, grad_losses, eta_alpha):
    """
    Update alpha weights for the Common Good algorithm.
    
    Args:
        alpha_current: 1D array of length k, current mixing weights (sum to 1)
        grad_losses: 2D array of shape (k, d), gradients of loss for each group
        eta_alpha: positive scalar step size
    
    Returns:
        1D array of length k, normalized updated alpha weights
    """
    # Convert inputs to numpy arrays
    alpha_current = np.asarray(alpha_current, dtype=float)
    grad_losses = np.asarray(grad_losses, dtype=float)
    eta_alpha = float(eta_alpha)
    
    k = len(alpha_current)
    
    # Compute sum of all group gradients
    sum_grad = np.sum(grad_losses, axis=0)
    
    # Initialize new alpha
    alpha_new = np.zeros(k, dtype=float)
    
    # Update each alpha_i
    for i in range(k):
        # Compute inner product between grad_losses[i] and sum_grad
        inner_prod_i = np.dot(grad_losses[i], sum_grad)
        
        # Update: alpha_new[i] = alpha_current[i] * exp(eta_alpha * inner_prod_i)
        alpha_new[i] = alpha_current[i] * np.exp(eta_alpha * inner_prod_i)
    
    # Normalize by L1 norm
    l1_norm = np.sum(np.abs(alpha_new))
    alpha_new = alpha_new / l1_norm
    
    return alpha_new
