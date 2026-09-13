import numpy as np

def variance_reduced_gradient_step(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk):
    """
    Compute the variance-reduced gradient estimator g^k for the L-SVRHG algorithm.

    Parameters:
    grad_H_ij_xk (array-like): The stochastic Hamiltonian gradient ∇H_{i,j}(x^k) evaluated at current point x^k with fresh samples i,j.
    grad_H_ij_wk (array-like): The stochastic Hamiltonian gradient ∇H_{i,j}(w^k) evaluated at snapshot point w^k with the same samples i,j.
    grad_H_wk (array-like): The full-batch Hamiltonian gradient ∇H(w^k) evaluated at snapshot point w^k.

    Returns:
    g^k (numpy array): The variance-reduced gradient estimator.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    grad_H_ij_xk = np.asarray(grad_H_ij_xk, dtype=float)
    grad_H_ij_wk = np.asarray(grad_H_ij_wk, dtype=float)
    grad_H_wk = np.asarray(grad_H_wk, dtype=float)

    # Compute g^k = ∇H_{i,j}(x^k) - ∇H_{i,j}(w^k) + ∇H(w^k)
    g_k = grad_H_ij_xk - grad_H_ij_wk + grad_H_wk

    return g_k
