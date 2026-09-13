import numpy as np


def gradient_acyclicity_constraint(W):
    """
    Compute the gradient of the acyclicity constraint h(W) with respect to W.
    
    The acyclicity constraint is:
        h(W) = trace((I + αW ⊙ W)^d) - d
    
    where:
        - α = 1/d
        - d is the number of nodes (W.shape[0])
        - ⊙ denotes element-wise product
        - I is the identity matrix
    
    The gradient is:
        ∇h(W) = α * ((I + αW ⊙ W)^(d-1))^T * (2W)
    
    where * denotes matrix multiplication and ^T denotes transpose.
    
    Args:
        W: Square numpy array of shape (d, d) representing edge weights
        
    Returns:
        Numpy array of shape (d, d) containing the gradient ∇h(W)
    """
    W = np.asarray(W, dtype=float)
    
    d = W.shape[0]
    alpha = 1.0 / d
    
    # Compute W ⊙ W (element-wise product)
    W_squared = W * W
    
    # Compute I + αW ⊙ W
    I = np.eye(d)
    M = I + alpha * W_squared
    
    # Compute M^(d-1) using matrix power
    M_power = np.linalg.matrix_power(M, d - 1)
    
    # Compute the gradient: α * (M^(d-1))^T * (2W)
    gradient = alpha * np.matmul(M_power.T, 2 * W)
    
    return gradient
