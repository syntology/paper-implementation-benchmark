import numpy as np

def laplace_marginal_likelihood_gradient(hessian_diag, prior_precision, n_data):
    """
    Compute the gradient of the log marginal likelihood with respect to the prior precision (gamma^2) 
    for a diagonal Laplace approximation.

    Parameters:
    hessian_diag (1D numpy array): Diagonal elements of the Hessian of the loss.
    prior_precision (float): Prior precision parameter (gamma^2).
    n_data (int): Number of data points (not used in the diagonal case).

    Returns:
    float: Gradient of the log marginal likelihood with respect to the prior precision.
    """
    hessian_diag = np.asarray(hessian_diag, dtype=float)
    prior_precision = float(prior_precision)
    n_data = int(n_data)  # Not used in this function

    # Compute the gradient
    gradient = -0.5 * np.sum(1 / (hessian_diag + prior_precision)) + 0.5 * len(hessian_diag) / prior_precision

    return float(gradient)
