import numpy as np


def simplex_projected_jacobian(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g, n_bins):
    """
    Compute the SimplEx projected Jacobian matrix.
    
    Args:
        x_test: 1D array of shape (d_X,) - test input
        h_test: 1D array of shape (d_H,) - test representation
        x_corpus: 2D array of shape (C, d_X) - corpus inputs
        h_corpus: 2D array of shape (C, d_H) - corpus representations
        x_baseline: 1D array of shape (d_X,) - baseline input
        h_baseline: 1D array of shape (d_H,) - baseline representation
        jacobian_g: 4D array of shape (C, n_bins, d_H, d_X) - precomputed Jacobians
        n_bins: positive integer - number of bins for path integration
    
    Returns:
        P: 2D array of shape (C, d_X) - projected Jacobian matrix
    """
    # Convert inputs to numpy arrays with float dtype
    x_test = np.asarray(x_test, dtype=float)
    h_test = np.asarray(h_test, dtype=float)
    x_corpus = np.asarray(x_corpus, dtype=float)
    h_corpus = np.asarray(h_corpus, dtype=float)
    x_baseline = np.asarray(x_baseline, dtype=float)
    h_baseline = np.asarray(h_baseline, dtype=float)
    jacobian_g = np.asarray(jacobian_g, dtype=float)
    
    # Get dimensions
    C = x_corpus.shape[0]  # corpus size
    d_X = x_corpus.shape[1]  # input dimension
    d_H = h_test.shape[0]  # representation dimension
    
    # Step 1: Initialize projection matrix P as zeros of shape (C, d_X)
    P = np.zeros((C, d_X), dtype=np.float64)
    
    # Step 2: Broadcast x_baseline to shape (C, d_X)
    X_0 = np.tile(x_baseline, (C, 1))  # shape (C, d_X)
    
    # Compute direction vector v = (h_test - h_baseline) / ||h_test - h_baseline||_2^2
    h_diff = h_test - h_baseline
    h_diff_norm_sq = np.sum(h_diff ** 2)  # L2 norm squared
    v = h_diff / h_diff_norm_sq  # shape (d_H,)
    
    # Step 3: Loop over bins (0-indexed, from 0 to n_bins-1)
    for n in range(n_bins):
        # Step 3a: Compute interpolated input
        # X_tilde = X^0 + ((n+1)/n_bins) * (x_corpus - X^0)
        alpha = (n + 1) / n_bins
        X_tilde = X_0 + alpha * (x_corpus - X_0)  # shape (C, d_X)
        
        # Step 3c: Increment P[c, i] by dot product of jacobian_g[c, n, :, i] with v
        # For each corpus example c and input dimension i:
        # P[c, i] += jacobian_g[c, n, :, i] · v
        # This can be vectorized as: P += jacobian_g[c, n, :, :].T @ v
        for c in range(C):
            # jacobian_g[c, n] has shape (d_H, d_X)
            # We want to compute: jacobian_g[c, n, :, i] · v for all i
            # This is equivalent to: v^T @ jacobian_g[c, n, :, :]
            P[c, :] += np.dot(v, jacobian_g[c, n, :, :])  # shape (d_X,)
    
    # Step 4: Apply element-wise multiplication
    # P = (1/n_bins) * (x_corpus - X_0) * P
    P = (1.0 / n_bins) * (x_corpus - X_0) * P
    
    return P.astype(np.float64)
