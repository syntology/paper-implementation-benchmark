import numpy as np


def compute_gbdt_residual_targets(x_prime, f_x):
    """
    Compute the residual targets for the next GBDT iteration in BGNN.
    
    This implements the step: Y_new = x_prime - f_x
    where x_prime is the learned node features from GNN training,
    and f_x is the current GBDT predictions on original features.
    
    Parameters
    ----------
    x_prime : array-like of shape (N, D)
        Learned node features output from GNN training step
    f_x : array-like of shape (N, D)
        Current GBDT predictions f(X) on original features
    
    Returns
    -------
    residual : ndarray of shape (N, D), dtype float64
        Element-wise residual: x_prime - f_x
    """
    # Convert inputs to numpy arrays with float dtype
    x_prime = np.asarray(x_prime, dtype=float)
    f_x = np.asarray(f_x, dtype=float)
    
    # Compute element-wise residual
    residual = x_prime - f_x
    
    # Ensure output is float64
    return residual.astype(np.float64)
