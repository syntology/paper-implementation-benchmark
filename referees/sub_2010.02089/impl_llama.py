import numpy as np

def copulagnn_conditional_mean_covariance(R, z_obs):
    """
    Compute the conditional mean and covariance for a Gaussian copula given observed transformed values.

    Parameters:
    R (numpy array): Correlation matrix of shape (n, n) where n = m + k, with m observed nodes and k unobserved nodes.
    z_obs (numpy array): 1D array of length m containing the transformed observed values (already mapped through Phi^{-1}).

    Returns:
    tuple: (mu_cond, Sigma_cond) where mu_cond is a 1D array of length k and Sigma_cond is a 2D array of shape (k, k).
    """
    R = np.asarray(R, dtype=float)
    z_obs = np.asarray(z_obs, dtype=float)

    m = len(z_obs)
    k = R.shape[0] - m

    # Partition the correlation matrix R
    R_00 = R[:m, :m]
    R_01 = R[:m, m:]
    R_10 = R[m:, :m]
    R_11 = R[m:, m:]

    # Compute the conditional mean
    mu_cond = np.dot(R_10, np.linalg.solve(R_00, z_obs))

    # Compute the conditional covariance
    Sigma_cond = R_11 - np.dot(R_10, np.linalg.solve(R_00, R_01))

    return mu_cond, Sigma_cond
