import numpy as np


def gaussian_label_loss(y_pred, y_true):
    """
    Compute the mean squared error loss for regression unlearning.
    
    Args:
        y_pred: 1D numpy array of shape (n,) containing predicted labels
        y_true: 1D numpy array of shape (n,) containing true labels
    
    Returns:
        float: The mean squared error loss (1/n) * sum((y_pred - y_true)^2)
    """
    y_pred = np.asarray(y_pred, dtype=float)
    y_true = np.asarray(y_true, dtype=float)
    
    # Compute squared differences
    squared_diff = (y_pred - y_true) ** 2
    
    # Compute mean
    mse = np.mean(squared_diff)
    
    # Return as plain Python float
    return float(mse)
