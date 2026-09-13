import numpy as np

def compute_conformal_epsilon(nonconformity_scores, alpha):
    """
    Compute the conformal prediction threshold epsilon from calibration nonconformity scores and significance level alpha.

    Parameters:
    nonconformity_scores (array-like): 1D array of shape (n,) containing non-negative floats representing calibration residuals.
    alpha (float): float in (0,1) representing the significance level.

    Returns:
    float: a single float representing the threshold epsilon.
    """
    nonconformity_scores = np.asarray(nonconformity_scores, dtype=float)
    alpha = float(alpha)

    # Sort nonconformity scores in ascending order
    sorted_scores = np.sort(nonconformity_scores)

    # Compute the index k
    n = len(nonconformity_scores)
    k = int(np.ceil((n + 1) * (1 - alpha))) - 1

    # If k >= n, return the maximum value in nonconformity scores
    if k >= n:
        return float(np.max(nonconformity_scores))
    # Otherwise return the k-th element of the sorted array
    else:
        return float(sorted_scores[k])
