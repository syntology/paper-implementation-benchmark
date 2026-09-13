import numpy as np


def is_mbpg_momentum_update(u_prev, g_current_theta_t, g_current_theta_prev, w_ratio, beta_t):
    """
    Compute the momentum update for IS-MBPG* algorithm at iteration t > 1.
    
    Parameters
    ----------
    u_prev : array-like
        Previous momentum vector u_{t-1}
    g_current_theta_t : array-like
        Policy gradient g(tau_t | theta_t) evaluated at current parameters
    g_current_theta_prev : array-like
        Policy gradient g(tau_t | theta_{t-1}) evaluated at previous parameters
    w_ratio : float
        Importance weight ratio w(tau_t | theta_{t-1}, theta_t)
    beta_t : float
        Momentum coefficient at iteration t
    
    Returns
    -------
    u_t : ndarray
        Updated momentum vector according to IS-MBPG* formula
    """
    # Convert inputs to numpy arrays
    u_prev = np.asarray(u_prev, dtype=float)
    g_current_theta_t = np.asarray(g_current_theta_t, dtype=float)
    g_current_theta_prev = np.asarray(g_current_theta_prev, dtype=float)
    w_ratio = float(w_ratio)
    beta_t = float(beta_t)
    
    # Compute u_t according to the IS-MBPG* formula:
    # u_t = beta_t * g(tau_t | theta_t) + (1 - beta_t) * [u_{t-1} + g(tau_t | theta_t) - w * g(tau_t | theta_{t-1})]
    
    # First term: beta_t * g(tau_t | theta_t)
    term1 = beta_t * g_current_theta_t
    
    # Second term: (1 - beta_t) * [u_{t-1} + g(tau_t | theta_t) - w * g(tau_t | theta_{t-1})]
    correction = g_current_theta_t - w_ratio * g_current_theta_prev
    term2 = (1.0 - beta_t) * (u_prev + correction)
    
    # Combine terms
    u_t = term1 + term2
    
    return u_t
