import numpy as np


def compute_variance_reduced_gradient(full_grad_at_w, local_grad_at_w):
    """
    Compute the variance-reduced gradient correction term g_k for SVRP.
    
    In the SVRP algorithm, the gradient correction term is computed as:
        g_k = ∇f(w_k) - ∇f_{m_k}(w_k)
    
    where:
    - ∇f(w_k) is the full gradient at the cached model w_k (averaged over all M clients)
    - ∇f_{m_k}(w_k) is the local gradient of sampled client m_k at w_k
    
    This correction term provides variance reduction by accounting for the difference
    between the full gradient and the local gradient at the cached point.
    
    Parameters
    ----------
    full_grad_at_w : array-like, shape (d,)
        The full gradient ∇f(w_k) averaged over all M clients at the cached model w_k
    local_grad_at_w : array-like, shape (d,)
        The local gradient ∇f_{m_k}(w_k) of the sampled client m_k at w_k
    
    Returns
    -------
    g_k : ndarray, shape (d,)
        The variance-reduced gradient correction term
    """
    full_grad_at_w = np.asarray(full_grad_at_w, dtype=float)
    local_grad_at_w = np.asarray(local_grad_at_w, dtype=float)
    
    # Compute g_k = ∇f(w_k) - ∇f_{m_k}(w_k)
    g_k = full_grad_at_w - local_grad_at_w
    
    return g_k
