import numpy as np


def compute_multiforward_regularization(losses, edge_indices):
    """
    Compute the multi-forward regularization term from Pareto Manifold Learning.
    
    Args:
        losses: float array of shape (W, T) where W is window size and T is number of tasks.
                losses[i, t] is the loss of task t for sample i.
        edge_indices: list of T arrays, where edge_indices[t] is an integer array of shape (E_t, 2)
                     containing pairs of indices (i, j) representing edges in the multi-forward graph
                     for task t.
    
    Returns:
        float: The multi-forward regularization term computed as:
               sum_{t=0}^{T-1} log( (1/E_t) * sum_{(i,j) in edges_t} exp(max(0, losses[i,t] - losses[j,t])) )
    """
    losses = np.asarray(losses, dtype=float)
    
    W, T = losses.shape
    
    total_regularization = 0.0
    
    for t in range(T):
        edges_t = np.asarray(edge_indices[t], dtype=float)
        
        # If no edges for this task, skip it (contribute 0)
        if edges_t.size == 0 or len(edges_t) == 0:
            continue
        
        E_t = edges_t.shape[0]
        
        # Compute sum over edges
        edge_sum = 0.0
        for edge_idx in range(E_t):
            i = int(edges_t[edge_idx, 0])
            j = int(edges_t[edge_idx, 1])
            
            # Compute [losses[i,t] - losses[j,t]]_+ where [x]_+ = max(0, x)
            loss_diff = losses[i, t] - losses[j, t]
            loss_diff_positive = max(0.0, loss_diff)
            
            # Add exp of the positive part
            edge_sum += np.exp(loss_diff_positive)
        
        # Compute average and take log
        average = edge_sum / E_t
        log_average = np.log(average)
        
        total_regularization += log_average
    
    return float(total_regularization)
