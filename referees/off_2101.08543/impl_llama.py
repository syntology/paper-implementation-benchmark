import numpy as np

def compute_gbdt_residual_targets(x_prime, f_x):
    """
    Compute the residual targets for the next GBDT iteration in the BGNN algorithm.

    Parameters:
    x_prime (array-like): Learned node features from GNN training, shape (N, D)
    f_x (array-like): Current GBDT predictions, shape (N, D)

    Returns:
    numpy array: Residual targets for the next GBDT iteration, shape (N, D)
    """
    # Convert array-like arguments to numpy arrays with dtype float64
    x_prime = np.asarray(x_prime, dtype=float)
    f_x = np.asarray(f_x, dtype=float)

    # Compute the residual targets using element-wise subtraction
    residual_targets = x_prime - f_x

    return residual_targets
