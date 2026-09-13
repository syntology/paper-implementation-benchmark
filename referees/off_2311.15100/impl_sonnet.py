import numpy as np


def uot_fm_loss(v_theta, t, x_t, u_t):
    """
    Compute the Flow Matching loss for Unbalanced Optimal Transport.
    
    Loss: ||v_θ(t, x_t) - u_t(x_t|x_1)||^2
    
    Args:
        v_theta: Predicted velocity field, shape (N, D)
        t: Scalar time value in [0, 1] (provided for interface completeness)
        x_t: Interpolated point at time t, shape (N, D)
        u_t: Target velocity field (x_1 - x_0), shape (N, D)
    
    Returns:
        Scalar float representing mean squared error over all N*D elements
    """
    v_theta = np.asarray(v_theta, dtype=float)
    u_t = np.asarray(u_t, dtype=float)
    
    # Compute squared difference
    diff = v_theta - u_t
    squared_diff = diff ** 2
    
    # Mean over all elements
    loss = np.mean(squared_diff)
    
    return float(loss)
