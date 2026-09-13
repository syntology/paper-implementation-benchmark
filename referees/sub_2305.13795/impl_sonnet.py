import numpy as np


def combine_gradients_with_coefficients(grad_f, grad_m, c):
    """
    Compute a combined gradient direction by linearly combining the fitness gradient
    and measure gradients with sampled coefficients.
    
    This implements the line from PPGA algorithm:
    nabla_i <- c_0 * nabla_f + sum_{j=1}^{k} c_j * nabla_m_j
    
    Args:
        grad_f: Array of shape (D,) representing the normalized gradient of the fitness function
        grad_m: Array of shape (k, D) representing k normalized measure gradients each of dimension D
        c: Array of shape (k+1,) representing gradient coefficients sampled from N(mu, Sigma)
           where c[0] multiplies grad_f, c[1:] multiply grad_m[0:k]
    
    Returns:
        nabla: Array of shape (D,) representing the combined gradient direction
    """
    grad_f = np.asarray(grad_f, dtype=float)
    grad_m = np.asarray(grad_m, dtype=float)
    c = np.asarray(c, dtype=float)
    
    # c[0] * grad_f
    nabla = c[0] * grad_f
    
    # sum_{j=1}^{k} c[j] * grad_m[j-1]
    # c[1] multiplies grad_m[0], c[2] multiplies grad_m[1], etc.
    k = grad_m.shape[0]
    for j in range(k):
        nabla += c[j + 1] * grad_m[j]
    
    return nabla
