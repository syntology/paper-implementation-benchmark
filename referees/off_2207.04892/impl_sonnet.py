import numpy as np


def adversarial_style_update(mu, sigma, grad_mu, grad_sigma, gamma):
    """
    Performs one step of adversarial style feature optimization (Eq. 3).
    
    Updates adversarial style features using gradient ascent to maximize
    the segmentation loss (or equivalently, minimize the negative loss).
    
    Args:
        mu: Channel-wise mean, shape [C]
        sigma: Channel-wise standard deviation, shape [C]
        grad_mu: Gradient of negative segmentation loss w.r.t. mu, shape [C]
        grad_sigma: Gradient of negative segmentation loss w.r.t. sigma, shape [C]
        gamma: Adversarial learning rate (scalar)
    
    Returns:
        tuple: (mu_plus, sigma_plus) where both are 1D numpy arrays of shape [C]
               containing the updated adversarial style features
    """
    # Convert inputs to numpy arrays with float dtype
    mu = np.asarray(mu, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    grad_mu = np.asarray(grad_mu, dtype=float)
    grad_sigma = np.asarray(grad_sigma, dtype=float)
    gamma = float(gamma)
    
    # Gradient ascent update (Eq. 3 from the paper)
    # Since we're maximizing the negative segmentation loss (minimizing segmentation loss),
    # we perform gradient ascent on the adversarial style features
    mu_plus = mu + gamma * grad_mu
    sigma_plus = sigma + gamma * grad_sigma
    
    return (mu_plus, sigma_plus)
