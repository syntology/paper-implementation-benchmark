import numpy as np

def adversarial_style_update(mu, sigma, grad_mu, grad_sigma, gamma):
    """
    Performs one step of adversarial style feature optimization as described in Eq. 3 of the AdvStyle paper.

    Args:
    mu (array-like): Current channel-wise mean.
    sigma (array-like): Current standard deviation.
    grad_mu (array-like): Gradient of the negative segmentation loss with respect to mu.
    grad_sigma (array-like): Gradient of the negative segmentation loss with respect to sigma.
    gamma (float): Adversarial learning rate.

    Returns:
    tuple: A tuple containing the updated adversarial style features mu_plus and sigma_plus.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    mu = np.asarray(mu, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    grad_mu = np.asarray(grad_mu, dtype=float)
    grad_sigma = np.asarray(grad_sigma, dtype=float)

    # Update the adversarial style features using gradient ascent
    mu_plus = mu + gamma * grad_mu
    sigma_plus = sigma + gamma * grad_sigma

    return mu_plus, sigma_plus
