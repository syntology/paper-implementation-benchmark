import numpy as np

def weighted_meta_gradient_aggregation(task_gradients, task_weights):
    """
    Compute the weighted sum of task-specific meta-gradients for outer-loop optimization in meta-learning.

    Args:
    task_gradients (2D array): Shape (B, D) where row i contains the gradient for task i.
    task_weights (1D array): Length B containing non-negative weights.

    Returns:
    1D array: Length D, the weighted sum of task-specific meta-gradients.
    """
    task_gradients = np.asarray(task_gradients, dtype=float)
    task_weights = np.asarray(task_weights, dtype=float)

    # Ensure task_weights are non-negative
    assert np.all(task_weights >= 0), "Task weights must be non-negative"

    # Compute the weighted sum of task-specific meta-gradients
    weighted_sum = np.sum(task_gradients * task_weights[:, np.newaxis], axis=0)

    return weighted_sum
