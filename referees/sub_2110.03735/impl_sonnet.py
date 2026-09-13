import numpy as np

def project_delta_to_l2_ball(delta, c_delta):
    """
    Projects a perturbation vector delta onto an L2 ball of radius c_delta.
    
    Args:
        delta: 1D array-like of shape (d,) representing the perturbation vector
        c_delta: positive scalar representing the L2 norm bound
    
    Returns:
        1D numpy array of shape (d,) with the projected perturbation
    """
    delta = np.asarray(delta, dtype=float)
    c_delta = float(c_delta)
    
    # Compute L2 norm of delta
    l2_norm = np.sqrt(np.sum(delta ** 2))
    
    # Project delta onto L2 ball: delta * min(1, c_delta / ||delta||_2)
    scaling_factor = min(1.0, c_delta / l2_norm)
    
    return delta * scaling_factor
