import numpy as np

def fastshap_loss(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, normalize):
    """
    Compute the FastSHAP loss for a single (x, y) pair.

    Parameters:
    phi_hat (1D numpy array): predicted Shapley values for d features
    v_all (float scalar): value function v(1) evaluated at all-ones vector of length d
    v_empty (float scalar): value function v(0) evaluated at all-zeros vector of length d
    v_samples (1D numpy array): value function v(s) evaluated at each subset s in s_samples
    s_samples (2D numpy array): binary (0 or 1) subset indicator vectors, one per row
    gamma (float scalar): penalty parameter for efficiency constraint
    normalize (boolean): if True apply efficiency normalization to phi_hat before computing approximation loss

    Returns:
    float scalar: total loss
    """
    # Convert array-like arguments to numpy arrays with float dtype
    phi_hat = np.asarray(phi_hat, dtype=float)
    v_samples = np.asarray(v_samples, dtype=float)
    s_samples = np.asarray(s_samples, dtype=float)

    # Compute efficiency penalty
    efficiency_penalty = (v_all - v_empty - np.sum(phi_hat)) ** 2

    # Apply efficiency normalization if required
    if normalize:
        phi_hat_adjusted = phi_hat + (v_all - v_empty - np.sum(phi_hat)) / len(phi_hat)
    else:
        phi_hat_adjusted = phi_hat

    # Compute squared errors for each sample
    squared_errors = (v_samples - v_empty - np.dot(s_samples, phi_hat_adjusted)) ** 2

    # Compute approximation loss
    approximation_loss = np.sum(squared_errors) / len(squared_errors)

    # Compute total loss
    total_loss = approximation_loss + gamma * efficiency_penalty

    return float(total_loss)
