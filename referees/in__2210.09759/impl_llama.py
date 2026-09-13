import numpy as np

def compute_multiforward_regularization(losses, edge_indices):
    """
    Compute the multi-forward regularization term from Pareto Manifold Learning.

    Parameters:
    losses (float array of shape (W, T)): losses[i, t] is the loss of task t for sample i.
    edge_indices (list of T arrays): edge_indices[t] is an integer array of shape (E_t, 2) containing pairs of indices (i, j) representing edges in the multi-forward graph for task t.

    Returns:
    float: sum_{t=0}^{T-1} log( (1/E_t) * sum_{(i,j) in edges_t} exp(max(0, losses[i,t] - losses[j,t])) )
    """
    losses = np.asarray(losses, dtype=float)
    edge_indices = [np.asarray(indices, dtype=int) for indices in edge_indices]

    def compute_task_regularization(losses, edge_indices):
        """
        Compute the regularization term for a single task.

        Parameters:
        losses (float array of shape (W,)): losses of the task for all samples.
        edge_indices (integer array of shape (E, 2)): pairs of indices (i, j) representing edges in the multi-forward graph.

        Returns:
        float: log( (1/E) * sum_{(i,j) in edges} exp(max(0, losses[i] - losses[j])) )
        """
        if len(edge_indices) == 0:
            return 0.0

        edge_losses = np.exp(np.maximum(0, losses[edge_indices[:, 0]] - losses[edge_indices[:, 1]]))
        return np.log(np.mean(edge_losses))

    task_regularizations = [compute_task_regularization(losses[:, t], edge_indices[t]) for t in range(losses.shape[1])]
    return sum(task_regularizations)
