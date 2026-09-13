import numpy as np

def stable_target_field(x_t, B_L, t, alpha_bar_t):
    """
    Compute the stable target field v_{B_L}(x_t) for a single perturbed sample.
    
    Args:
        x_t: 1D array of shape (D,) representing the perturbed sample
        B_L: 2D array of shape (N, D) where N is number of reference samples
        t: scalar time value (unused but kept for API consistency)
        alpha_bar_t: scalar in (0,1) representing cumulative product of alphas
    
    Returns:
        1D array of shape (D,) representing the stable target field
    """
    # Convert inputs to numpy arrays
    x_t = np.asarray(x_t, dtype=float)
    B_L = np.asarray(B_L, dtype=float)
    alpha_bar_t = float(alpha_bar_t)
    
    # Get dimensions
    N, D = B_L.shape
    
    # Compute sqrt(alpha_bar_t) * x for all reference samples
    sqrt_alpha_bar_t = np.sqrt(alpha_bar_t)
    scaled_B_L = sqrt_alpha_bar_t * B_L  # Shape: (N, D)
    
    # Compute differences: x_t - sqrt(alpha_bar_t) * x for each reference sample
    # Broadcasting: x_t has shape (D,), scaled_B_L has shape (N, D)
    diff = x_t[np.newaxis, :] - scaled_B_L  # Shape: (N, D)
    
    # Compute squared norms for each reference sample
    squared_norms = np.sum(diff ** 2, axis=1)  # Shape: (N,)
    
    # Compute log probabilities: log p_{t|0}(x_t|x)
    # log p = -0.5 * ||x_t - sqrt(alpha_bar_t)*x||^2 / (1-alpha_bar_t) - D/2*log(2*pi*(1-alpha_bar_t))
    variance = 1.0 - alpha_bar_t
    log_probs = -0.5 * squared_norms / variance - 0.5 * D * np.log(2 * np.pi * variance)
    
    # Convert to unnormalized weights (numerically stable)
    # Subtract max for numerical stability
    log_probs_shifted = log_probs - np.max(log_probs)
    weights = np.exp(log_probs_shifted)  # Shape: (N,)
    
    # Normalize weights
    weights_sum = np.sum(weights)
    normalized_weights = weights / weights_sum  # Shape: (N,)
    
    # Compute scores: nabla_{x_t} log p_{t|0}(x_t|x) = -(x_t - sqrt(alpha_bar_t)*x) / (1-alpha_bar_t)
    scores = -diff / variance  # Shape: (N, D)
    
    # Compute weighted sum of scores
    # v_{B_L}(x_t) = sum_i w_i_normalized * score_i
    stable_target = np.sum(normalized_weights[:, np.newaxis] * scores, axis=0)  # Shape: (D,)
    
    return stable_target
