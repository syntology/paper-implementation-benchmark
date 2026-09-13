import numpy as np

def _l2_norm_squared(x):
    """
    Compute the squared Euclidean L2 norm of a vector.
    
    Parameters:
    x (np.ndarray): Input vector.
    
    Returns:
    float: Squared Euclidean L2 norm of the input vector.
    """
    return np.sum(x ** 2)

def uot_fm_loss(v_theta, t, x_t, u_t):
    """
    Compute the Flow Matching loss for Unbalanced Optimal Transport.
    
    Parameters:
    v_theta (array-like): Predicted velocity field, shape (N, D).
    t (float): Scalar time value in [0,1].
    x_t (array-like): Interpolated point at time t, shape (N, D).
    u_t (array-like): Target velocity field, shape (N, D).
    
    Returns:
    float: Mean squared error between v_theta and u_t.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    v_theta = np.asarray(v_theta, dtype=float)
    u_t = np.asarray(u_t, dtype=float)
    
    # Compute the difference between v_theta and u_t
    diff = v_theta - u_t
    
    # Compute the squared Euclidean L2 norm of the difference
    squared_norm = _l2_norm_squared(diff)
    
    # Compute the mean squared error
    mse = squared_norm / (v_theta.shape[0] * v_theta.shape[1])
    
    return mse
