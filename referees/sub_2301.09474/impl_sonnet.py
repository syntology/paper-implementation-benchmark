import numpy as np


def difformer_update_step(x_current, x_residual, tau):
    """
    Compute one DIFFormer propagation update step combining the current layer
    output with a residual connection.
    
    Args:
        x_current: Output from the current convolution layer, shape [N, D]
        x_residual: Residual connection from the previous layer, shape [N, D]
        tau: Scalar step size in range [0, 1]
    
    Returns:
        x_new: Updated features, shape [N, D]
    """
    x_current = np.asarray(x_current, dtype=float)
    x_residual = np.asarray(x_residual, dtype=float)
    tau = float(tau)
    
    # DIFFormer update: x = tau * x + (1-tau) * layer_[i]
    x_new = tau * x_current + (1 - tau) * x_residual
    
    return x_new
