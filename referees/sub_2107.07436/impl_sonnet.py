import numpy as np

def fastshap_loss(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, normalize):
    """
    Compute the FastSHAP loss for a single (x, y) pair.
    
    Args:
        phi_hat: 1D numpy array of shape (d,), predicted Shapley values
        v_all: float scalar, value function v(1) at all-ones vector
        v_empty: float scalar, value function v(0) at all-zeros vector
        v_samples: 1D numpy array of shape (m,), value function v(s) for each subset
        s_samples: 2D numpy array of shape (m, d), binary subset indicators
        gamma: float scalar >= 0, penalty parameter
        normalize: boolean, if True apply efficiency normalization
    
    Returns:
        total_loss: float scalar
    """
    # Convert inputs to numpy arrays with float dtype
    phi_hat = np.asarray(phi_hat, dtype=float)
    v_all = float(v_all)
    v_empty = float(v_empty)
    v_samples = np.asarray(v_samples, dtype=float)
    s_samples = np.asarray(s_samples, dtype=float)
    gamma = float(gamma)
    
    d = phi_hat.shape[0]
    m = v_samples.shape[0]
    
    # Step 1: Compute efficiency penalty
    phi_sum = np.sum(phi_hat)
    efficiency_gap = v_all - v_empty - phi_sum
    efficiency_penalty = efficiency_gap ** 2
    
    # Step 2: Apply normalization if requested
    if normalize:
        phi_hat_adjusted = phi_hat + efficiency_gap / d
    else:
        phi_hat_adjusted = phi_hat
    
    # Step 3: Compute squared errors for each sample
    squared_errors = np.zeros(m)
    for i in range(m):
        dot_product = np.dot(s_samples[i], phi_hat_adjusted)
        squared_errors[i] = (v_samples[i] - v_empty - dot_product) ** 2
    
    # Step 4: Compute approximation loss (mean of squared errors)
    approximation_loss = np.sum(squared_errors) / m
    
    # Step 5: Compute total loss
    total_loss = approximation_loss + gamma * efficiency_penalty
    
    # Step 6: Return as plain Python float
    return float(total_loss)
