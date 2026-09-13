import numpy as np


def laplace_marginal_likelihood_gradient(hessian_diag, prior_precision, n_data):
    """
    Compute the gradient of the log marginal likelihood with respect to the prior precision
    for a diagonal Laplace approximation.
    
    The log marginal likelihood (evidence) for Laplace approximation is:
        log p(D|gamma^2) = -0.5 * sum(log(hessian_diag + prior_precision)) 
                          + 0.5 * n_params * log(prior_precision) + const
    
    The gradient with respect to prior_precision is:
        d/d(prior_precision) log p(D|gamma^2) = -0.5 * sum(1 / (hessian_diag + prior_precision))
                                                 + 0.5 * n_params / prior_precision
    
    Args:
        hessian_diag: 1D array of shape (n_params,) containing diagonal elements of the Hessian
        prior_precision: Scalar prior precision parameter (gamma^2)
        n_data: Number of data points (included for completeness, not used in diagonal case)
    
    Returns:
        Scalar float representing the gradient
    """
    # Convert inputs to numpy arrays with float dtype
    hessian_diag = np.asarray(hessian_diag, dtype=float)
    prior_precision = float(prior_precision)
    
    # Get number of parameters
    n_params = len(hessian_diag)
    
    # Compute gradient: -0.5 * sum(1 / (hessian_diag + prior_precision)) + 0.5 * n_params / prior_precision
    term1 = -0.5 * np.sum(1.0 / (hessian_diag + prior_precision))
    term2 = 0.5 * n_params / prior_precision
    
    gradient = term1 + term2
    
    # Return as plain Python float
    return float(gradient)
