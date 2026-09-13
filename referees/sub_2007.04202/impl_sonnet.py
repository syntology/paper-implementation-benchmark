import numpy as np

def variance_reduced_gradient_step(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk):
    """
    Compute the variance-reduced gradient estimator g^k for L-SVRHG algorithm.
    
    Implements: g^k = ∇H_{i,j}(x^k) - ∇H_{i,j}(w^k) + ∇H(w^k)
    
    Args:
        grad_H_ij_xk: Stochastic Hamiltonian gradient at current point x^k with samples i,j
        grad_H_ij_wk: Stochastic Hamiltonian gradient at snapshot point w^k with same samples i,j
        grad_H_wk: Full-batch Hamiltonian gradient at snapshot point w^k
    
    Returns:
        g^k: Variance-reduced gradient estimator (1-dimensional numpy array)
    """
    # Convert inputs to numpy arrays with float dtype
    grad_H_ij_xk = np.asarray(grad_H_ij_xk, dtype=float)
    grad_H_ij_wk = np.asarray(grad_H_ij_wk, dtype=float)
    grad_H_wk = np.asarray(grad_H_wk, dtype=float)
    
    # Compute variance-reduced gradient: g^k = ∇H_{i,j}(x^k) - ∇H_{i,j}(w^k) + ∇H(w^k)
    g_k = grad_H_ij_xk - grad_H_ij_wk + grad_H_wk
    
    return g_k
