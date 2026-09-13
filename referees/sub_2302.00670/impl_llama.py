import numpy as np

def stable_target_field(x_t, B_L, t, alpha_bar_t):
    """
    Compute the stable target field v_{B_L}(x_t) for a single perturbed sample x_t at time t,
    given a large reference batch B_L of clean data samples.

    Parameters:
    x_t (array-like): 1D array of shape (D,) representing the perturbed sample.
    B_L (array-like): 2D array of shape (N, D) where N is the number of reference samples and D is the data dimension.
    t (scalar): unused in computation but kept for API consistency.
    alpha_bar_t (scalar): a scalar in (0,1) representing the cumulative product of alphas up to time t.

    Returns:
    v_{B_L}(x_t) (1D array of shape (D,)): the stable target field.
    """
    x_t = np.asarray(x_t, dtype=float)
    B_L = np.asarray(B_L, dtype=float)

    # Compute log probabilities
    log_probabilities = -0.5 * np.sum((x_t - np.sqrt(alpha_bar_t) * B_L) ** 2, axis=1) / (1 - alpha_bar_t) - B_L.shape[1] / 2 * np.log(2 * np.pi * (1 - alpha_bar_t))

    # Convert log probabilities to unnormalized weights
    weights = np.exp(log_probabilities)

    # Normalize weights
    normalized_weights = weights / np.sum(weights)

    # Compute scores
    scores = -(x_t - np.sqrt(alpha_bar_t) * B_L) / (1 - alpha_bar_t)

    # Compute the stable target field
    v_B_L = np.sum(normalized_weights[:, np.newaxis] * scores, axis=0)

    return v_B_L
