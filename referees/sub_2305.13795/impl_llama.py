import numpy as np

def combine_gradients_with_coefficients(grad_f, grad_m, c):
    """
    Compute a combined gradient direction by linearly combining the fitness gradient and measure gradients with sampled coefficients.

    Parameters:
    grad_f (array-like): The normalized gradient of the fitness function, shape (D,)
    grad_m (array-like): k normalized measure gradients each of dimension D, shape (k, D)
    c (array-like): Gradient coefficients sampled from N(mu, Sigma), shape (k+1,)

    Returns:
    nabla (numpy.ndarray): The combined gradient, shape (D,)
    """
    grad_f = np.asarray(grad_f, dtype=float)
    grad_m = np.asarray(grad_m, dtype=float)
    c = np.asarray(c, dtype=float)

    # Extract the coefficient for the fitness gradient
    c_f = c[0]

    # Extract the coefficients for the measure gradients
    c_m = c[1:]

    # Compute the combined gradient
    nabla = c_f * grad_f + np.sum(c_m[:, np.newaxis] * grad_m, axis=0)

    return nabla
