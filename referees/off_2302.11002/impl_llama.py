import numpy as np

def probconserv_update(mu, Sigma, G, b, sigma_G):
    """
    Implements the ProbConserv constraint update from equation (updated_mean_var) in arXiv:2302.11002.

    Parameters:
    mu (array-like): Gaussian prediction mean with shape (n,).
    Sigma (array-like): Gaussian prediction covariance with shape (n, n).
    G (array-like): Linear constraint matrix with shape (m, n).
    b (array-like): Linear constraint value with shape (m,).
    sigma_G (float): Constraint noise standard deviation.

    Returns:
    tuple: A tuple containing the constrained posterior mean (tilde_mu) and covariance (tilde_Sigma).
    """
    # Convert array-like arguments to numpy arrays with float dtype
    mu = np.asarray(mu, dtype=float)
    Sigma = np.asarray(Sigma, dtype=float)
    G = np.asarray(G, dtype=float)
    b = np.asarray(b, dtype=float)

    # Compute the constrained posterior mean and covariance
    temp = np.linalg.inv(G @ Sigma @ G.T + sigma_G**2 * np.eye(G.shape[0]))
    tilde_mu = mu + Sigma @ G.T @ temp @ (b - G @ mu)
    tilde_Sigma = Sigma - Sigma @ G.T @ temp @ G @ Sigma

    return tilde_mu, tilde_Sigma
