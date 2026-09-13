import numpy as np

def is_mbpg_momentum_update(u_prev, g_current_theta_t, g_current_theta_prev, w_ratio, beta_t):
    """
    Compute the momentum update for IS-MBPG* algorithm at iteration t > 1.

    Parameters:
    u_prev (array-like): Previous momentum vector.
    g_current_theta_t (array-like): Policy gradient evaluated at current parameters.
    g_current_theta_prev (array-like): Policy gradient evaluated at previous parameters.
    w_ratio (float): Importance weight ratio.
    beta_t (float): Momentum coefficient.

    Returns:
    u_t (numpy array): Updated momentum vector.
    """
    u_prev = np.asarray(u_prev, dtype=float)
    g_current_theta_t = np.asarray(g_current_theta_t, dtype=float)
    g_current_theta_prev = np.asarray(g_current_theta_prev, dtype=float)

    # Compute the update term
    update_term = u_prev + g_current_theta_t - w_ratio * g_current_theta_prev

    # Compute the momentum update
    u_t = beta_t * g_current_theta_t + (1 - beta_t) * update_term

    return u_t
