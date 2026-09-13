import numpy as np

def binary_cross_entropy_loss(y_pred, y_target):
    """
    Compute the binary cross-entropy (BCE) loss between predictions and targets.

    Args:
    y_pred (1D numpy array): Predicted probabilities in [0,1].
    y_target (1D numpy array): Binary labels (0 or 1).

    Returns:
    float: The mean BCE loss over all samples.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    y_pred = np.asarray(y_pred, dtype=float)
    y_target = np.asarray(y_target, dtype=float)

    # Clip y_pred values to the range [eps, 1-eps] for numerical stability
    eps = 1e-7
    y_pred = np.clip(y_pred, eps, 1 - eps)

    # Compute the BCE loss
    loss = -(y_target * np.log(y_pred) + (1 - y_target) * np.log(1 - y_pred))

    # Return the mean loss over all samples
    return np.mean(loss).item()

# Helper function to compute the natural logarithm with a small value added for stability
def _stable_log(x):
    return np.log(np.clip(x, 1e-7, 1 - 1e-7))

# However, the above helper function is not needed in this case, 
# as we are already clipping the values in the main function.
