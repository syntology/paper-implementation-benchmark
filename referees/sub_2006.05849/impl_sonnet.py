import numpy as np

def binary_cross_entropy_loss(y_pred, y_target):
    """
    Compute the binary cross-entropy (BCE) loss between predictions and targets.
    
    Args:
        y_pred: 1D array of shape (N,) containing predicted probabilities in [0,1]
        y_target: 1D array of shape (N,) containing binary labels (0 or 1)
    
    Returns:
        Scalar float representing the mean BCE loss over all N samples
    """
    # Convert inputs to numpy arrays with float dtype
    y_pred = np.asarray(y_pred, dtype=float)
    y_target = np.asarray(y_target, dtype=float)
    
    # Clip predictions for numerical stability
    eps = 1e-7
    y_pred_clipped = np.clip(y_pred, eps, 1 - eps)
    
    # Compute BCE loss
    # L = -(1/N) * sum[y_target * log(y_pred) + (1 - y_target) * log(1 - y_pred)]
    N = len(y_pred)
    
    loss = -np.mean(
        y_target * np.log(y_pred_clipped) + 
        (1 - y_target) * np.log(1 - y_pred_clipped)
    )
    
    # Return as plain Python float
    return float(loss)
