import numpy as np

def _mean_squared_error(y_pred, y_true):
    """
    Compute the mean squared error loss.

    Args:
    y_pred (np.ndarray): Predicted labels.
    y_true (np.ndarray): True labels.

    Returns:
    float: The mean squared error loss.
    """
    return np.mean((y_pred - y_true) ** 2)

def gaussian_label_loss(y_pred, y_true):
    """
    Compute the mean squared error loss for regression unlearning.

    Args:
    y_pred (np.ndarray): Predicted labels.
    y_true (np.ndarray): True labels.

    Returns:
    float: The mean squared error loss.
    """
    y_pred = np.asarray(y_pred, dtype=float)
    y_true = np.asarray(y_true, dtype=float)
    return float(_mean_squared_error(y_pred, y_true))
