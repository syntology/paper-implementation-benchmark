import numpy as np

def compute_variance_reduced_gradient(full_grad_at_w, local_grad_at_w):
    """
    Compute the variance-reduced gradient correction term g_k as defined in the SVRP algorithm.

    Parameters:
    full_grad_at_w (array-like): The full gradient at the cached model w_k (averaged over all M clients)
    local_grad_at_w (array-like): The local gradient of a single sampled client m_k at w_k

    Returns:
    g_k (numpy array): The gradient correction term
    """
    full_grad_at_w = np.asarray(full_grad_at_w, dtype=float)
    local_grad_at_w = np.asarray(local_grad_at_w, dtype=float)
    
    # Compute the variance-reduced gradient correction term g_k
    g_k = full_grad_at_w - local_grad_at_w
    
    return g_k
