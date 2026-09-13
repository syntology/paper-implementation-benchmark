import numpy as np


def copulagnn_conditional_mean_covariance(R, z_obs):
    """
    Compute the conditional mean and covariance for a Gaussian copula.
    
    Parameters
    ----------
    R : array-like, shape (n, n)
        Correlation matrix where n = m + k, with m observed nodes and k unobserved nodes.
    z_obs : array-like, shape (m,)
        Transformed observed values (already mapped through Phi^{-1}).
    
    Returns
    -------
    mu_cond : ndarray, shape (k,)
        Conditional mean vector.
    Sigma_cond : ndarray, shape (k, k)
        Conditional covariance matrix.
    """
    # Convert inputs to numpy arrays with float64 dtype
    R = np.asarray(R, dtype=float)
    z_obs = np.asarray(z_obs, dtype=float)
    
    # Get dimensions
    n = R.shape[0]
    m = z_obs.shape[0]
    k = n - m
    
    # Partition the correlation matrix R into blocks
    # R = [[R_00, R_01],
    #      [R_10, R_11]]
    R_00 = R[:m, :m]
    R_01 = R[:m, m:]
    R_10 = R[m:, :m]
    R_11 = R[m:, m:]
    
    # Compute the inverse of R_00
    R_00_inv = np.linalg.inv(R_00)
    
    # Compute conditional mean: mu_cond = R_10 @ inv(R_00) @ z_obs
    mu_cond = R_10 @ R_00_inv @ z_obs
    
    # Compute conditional covariance: Sigma_cond = R_11 - R_10 @ inv(R_00) @ R_01
    Sigma_cond = R_11 - R_10 @ R_00_inv @ R_01
    
    return mu_cond, Sigma_cond
