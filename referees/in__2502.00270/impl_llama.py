import numpy as np

def gp_lower_confidence_bound(mu_t, sigma_t, beta_t):
    """
    Compute the Lower Confidence Bound (LCB) acquisition function for Bayesian Optimization.

    Parameters:
    mu_t (array-like): Posterior mean at n candidate points.
    sigma_t (array-like): Posterior standard deviation at n candidate points.
    beta_t (float): Exploration parameter.

    Returns:
    array: A 1D numpy array of shape (n,) containing the LCB values.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    mu_t = np.asarray(mu_t, dtype=float)
    sigma_t = np.asarray(sigma_t, dtype=float)

    # Check if mu_t and sigma_t have identical shapes
    assert mu_t.shape == sigma_t.shape, "mu_t and sigma_t must have identical shapes"

    # Check if sigma_t values are non-negative
    assert np.all(sigma_t >= 0), "sigma_t values must be non-negative"

    # Check if beta_t is non-negative
    assert beta_t >= 0, "beta_t must be non-negative"

    # Compute LCB = mu_t - beta_t * sigma_t element-wise
    lcb = mu_t - beta_t * sigma_t

    return lcb
