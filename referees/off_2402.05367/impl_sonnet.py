import numpy as np


def compute_optimistic_preference_gain(x, x_ref, f_samples):
    """
    Compute the optimistic preferential gain for candidate point x relative to
    reference point x_ref over a set of function samples from the posterior
    confidence set.
    
    This implements the inner maximization from Algorithm 1 (POP-BO):
    max_{f in confidence_set}(f(x) - f(x_ref))
    
    Parameters
    ----------
    x : array-like of shape (d,)
        The candidate point in d-dimensional space.
    x_ref : array-like of shape (d,)
        The reference point in d-dimensional space.
    f_samples : array-like of shape (n_samples, n_points)
        Function samples from the posterior confidence set.
        Column 0: evaluations at x
        Column 1: evaluations at x_ref
        Additional columns are ignored.
    
    Returns
    -------
    float
        The maximum preferential gain across all function samples.
    """
    # Convert inputs to numpy arrays
    x = np.asarray(x, dtype=float)
    x_ref = np.asarray(x_ref, dtype=float)
    f_samples = np.asarray(f_samples, dtype=float)
    
    # Compute preference gain for each function sample
    # gain_i = f_samples[i, 0] - f_samples[i, 1]
    # where column 0 is f(x) and column 1 is f(x_ref)
    gains = f_samples[:, 0] - f_samples[:, 1]
    
    # Return the maximum gain across all samples
    max_gain = np.max(gains)
    
    return float(max_gain)
