import numpy as np

def difformer_update_step(x_current, x_residual, tau):
    """
    Compute one DIFFormer propagation update step combining the current layer output with a residual connection.

    Parameters:
    x_current (array-like): The output from the current convolution layer, shape [N, D] where N is number of nodes and D is feature dimension.
    x_residual (array-like): The residual connection from the previous layer, same shape [N, D].
    tau (float): Scalar step size in range [0,1].

    Returns:
    array-like: The updated features as a float array of shape [N, D].
    """
    # Convert array-like arguments to numpy arrays with float dtype
    x_current = np.asarray(x_current, dtype=float)
    x_residual = np.asarray(x_residual, dtype=float)
    tau = float(tau)

    # Compute the updated features using the DIFFormer update formula
    x_new = tau * x_current + (1 - tau) * x_residual

    return x_new
