import numpy as np


def weighted_meta_gradient_aggregation(task_gradients, task_weights):
    """
    Compute the weighted sum of task-specific meta-gradients for outer-loop optimization.
    
    This implements the outer-loop update step from Algorithm 1 (Meta-Training for VRPs):
    theta_0 <- theta_0 - beta * sum_{i=1}^{B} w_i * nabla_{theta_0} L_i(theta_i^{(K)})
    
    This function computes: sum_{i=1}^{B} w_i * g_i
    where g_i is the gradient from task i and w_i is its weight.
    
    Args:
        task_gradients: 2D array of shape (B, D) where B is the number of tasks
                       and D is the dimension of the flattened gradient vector.
                       Row i contains the gradient for task i.
        task_weights: 1D array of length B containing non-negative weights for each task.
                     Typically sums to 1.0 but need not be normalized.
    
    Returns:
        1D array of length D representing the weighted sum of gradients.
    """
    # Convert inputs to numpy arrays with float dtype
    task_gradients = np.asarray(task_gradients, dtype=float)
    task_weights = np.asarray(task_weights, dtype=float)
    
    # Compute weighted sum: sum_{i=1}^{B} w_i * g_i
    # Broadcasting: task_weights has shape (B,), need to reshape to (B, 1)
    # to multiply with task_gradients of shape (B, D)
    weighted_gradients = task_weights[:, np.newaxis] * task_gradients
    
    # Sum across tasks (axis 0) to get final gradient of shape (D,)
    aggregated_gradient = np.sum(weighted_gradients, axis=0)
    
    return aggregated_gradient
