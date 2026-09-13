import numpy as np


def gp_lower_confidence_bound(mu_t, sigma_t, beta_t):
    """
    Compute the Lower Confidence Bound (LCB) acquisition function for Bayesian Optimization.
    
    This implements the acquisition step from DUET algorithm (step 2):
    r_t = argmin_r (mu_t(r) - beta_t * sigma_t(r))
    
    The LCB acquisition function balances exploitation (low mean) and exploration 
    (high uncertainty). Lower LCB values are preferred.
    
    Args:
        mu_t: Posterior mean from GP, array-like of shape (n,)
        sigma_t: Posterior standard deviation from GP, array-like of shape (n,)
        beta_t: Exploration parameter, scalar float (non-negative)
    
    Returns:
        lcb: Lower confidence bound values, numpy array of shape (n,)
             lcb[i] = mu_t[i] - beta_t * sigma_t[i]
    """
    # Convert inputs to numpy arrays with float dtype
    mu_t = np.asarray(mu_t, dtype=float)
    sigma_t = np.asarray(sigma_t, dtype=float)
    beta_t = float(beta_t)
    
    # Compute LCB element-wise: mu_t - beta_t * sigma_t
    lcb = mu_t - beta_t * sigma_t
    
    return lcb
