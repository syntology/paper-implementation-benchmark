import numpy as np

def simplex_projected_jacobian(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g, n_bins):
    """
    Compute the SimplEx projected Jacobian matrix that explains a test representation using a corpus of examples.

    Parameters:
    x_test (array-like): 1D array of shape (d_X,) representing the test input.
    h_test (array-like): 1D array of shape (d_H,) representing the test representation.
    x_corpus (array-like): 2D array of shape (C, d_X) where C is the corpus size and d_X is the input dimension.
    h_corpus (array-like): 2D array of shape (C, d_H) where d_H is the representation dimension.
    x_baseline (array-like): 1D array of shape (d_X,).
    h_baseline (array-like): 1D array of shape (d_H,).
    jacobian_g (array-like): 3D array of shape (C, n_bins, d_H, d_X) containing precomputed Jacobian matrices ∂g/∂x evaluated at each corpus example c and each bin n.
    n_bins (int): Positive integer specifying the number of bins for path integration.

    Returns:
    P (2D array): SimplEx projected Jacobian matrix of shape (C, d_X) with dtype float64.
    """
    # Convert array-like arguments to numpy arrays with dtype float
    x_test = np.asarray(x_test, dtype=float)
    h_test = np.asarray(h_test, dtype=float)
    x_corpus = np.asarray(x_corpus, dtype=float)
    h_corpus = np.asarray(h_corpus, dtype=float)
    x_baseline = np.asarray(x_baseline, dtype=float)
    h_baseline = np.asarray(h_baseline, dtype=float)
    jacobian_g = np.asarray(jacobian_g, dtype=float)

    # Initialize projection matrix P as zeros of shape (C, d_X)
    C, d_X = x_corpus.shape
    P = np.zeros((C, d_X), dtype=float)

    # Broadcast x_baseline to shape (C, d_X) by repeating it C times to form X^0
    X_0 = np.tile(x_baseline, (C, 1))

    # Compute direction vector v = (h_test - h_baseline) / ||h_test - h_baseline||_2^2
    h_diff = h_test - h_baseline
    v = h_diff / np.linalg.norm(h_diff) ** 2

    # For each bin index n from 0 to n_bins-1 (inclusive, 0-indexed)
    for n in range(n_bins):
        # Compute interpolated input X_tilde = X^0 + ((n+1)/n_bins) * (x_corpus - X^0)
        X_tilde = X_0 + ((n + 1) / n_bins) * (x_corpus - X_0)

        # For each corpus example c and input dimension i, increment P[c, i] by the dot product of jacobian_g[c, n, :, i] with v
        for c in range(C):
            for i in range(d_X):
                P[c, i] += np.dot(jacobian_g[c, n, :, i], v)

    # Apply element-wise multiplication: P = (1/n_bins) * (x_corpus - X^0) * P
    P = (1 / n_bins) * (x_corpus - X_0) * P

    return P
