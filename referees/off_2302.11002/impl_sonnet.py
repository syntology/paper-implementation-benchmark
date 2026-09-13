import numpy as np


def probconserv_update(mu, Sigma, G, b, sigma_G):
    """
    Implements the ProbConserv constraint update from arXiv:2302.11002.
    
    Given a Gaussian prediction with mean mu and covariance Sigma, and linear
    constraints G @ y = b with noise sigma_G, compute the constrained posterior
    mean tilde_mu and covariance tilde_Sigma.
    
    Parameters
    ----------
    mu : array-like, shape (n,)
        Prior mean of the Gaussian prediction
    Sigma : array-like, shape (n, n)
        Prior covariance matrix of the Gaussian prediction
    G : array-like, shape (m, n)
        Constraint matrix representing m constraints on n outputs
    b : array-like, shape (m,)
        Constraint values
    sigma_G : float
        Constraint noise standard deviation (positive scalar)
    
    Returns
    -------
    tilde_mu : ndarray, shape (n,)
        Posterior mean after applying constraints
    tilde_Sigma : ndarray, shape (n, n)
        Posterior covariance after applying constraints
    """
    # Convert inputs to numpy arrays with float dtype
    mu = np.asarray(mu, dtype=float)
    Sigma = np.asarray(Sigma, dtype=float)
    G = np.asarray(G, dtype=float)
    b = np.asarray(b, dtype=float)
    sigma_G = float(sigma_G)
    
    # Get dimensions
    m = G.shape[0]  # number of constraints
    
    # Compute G @ Sigma @ G.T
    GSigma = G @ Sigma
    GSigmaGT = GSigma @ G.T
    
    # Add noise term: G @ Sigma @ G.T + sigma_G^2 * I
    noise_term = GSigmaGT + (sigma_G ** 2) * np.eye(m)
    
    # Compute the inverse of the noise term
    noise_term_inv = np.linalg.inv(noise_term)
    
    # Compute Sigma @ G.T @ inv(...)
    SigmaGT = Sigma @ G.T
    SigmaGT_inv = SigmaGT @ noise_term_inv
    
    # Compute posterior mean: tilde_mu = mu + Sigma @ G.T @ inv(...) @ (b - G @ mu)
    residual = b - G @ mu
    tilde_mu = mu + SigmaGT_inv @ residual
    
    # Compute posterior covariance: tilde_Sigma = Sigma - Sigma @ G.T @ inv(...) @ G @ Sigma
    tilde_Sigma = Sigma - SigmaGT_inv @ GSigma
    
    return tilde_mu, tilde_Sigma
