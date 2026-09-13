import numpy as np


def estimate_python_proportion(loss_j, alpha, beta):
    """
    Estimate the proportion of the Python system P(ℓ_j) based on Equation 1.
    
    This function computes how far the training loss has progressed from the
    initial state (alpha) toward the optimal state (beta).
    
    Args:
        loss_j: Training loss at checkpoint j (scalar float)
        alpha: Initial loss (scalar float)
        beta: Lowest loss (scalar float)
    
    Returns:
        float: The proportion P(ℓ_j) in [0, 1] under normal conditions
               where beta <= loss_j <= alpha
    
    Formula: P(ℓ_j) = (alpha - loss_j) / (alpha - beta)
    """
    # Convert inputs to float arrays then extract scalar values
    loss_j = np.asarray(loss_j, dtype=float).item()
    alpha = np.asarray(alpha, dtype=float).item()
    beta = np.asarray(beta, dtype=float).item()
    
    # Compute the proportion using Equation 1
    # P(ℓ_j) = (alpha - loss_j) / (alpha - beta)
    numerator = alpha - loss_j
    denominator = alpha - beta
    
    # Handle edge case where alpha == beta (no progress possible)
    if denominator == 0:
        return 0.0
    
    proportion = numerator / denominator
    
    return float(proportion)
