import numpy as np

def priorgrad_loss(epsilon, epsilon_theta, sigma):
    """
    Compute the PriorGrad weighted loss.

    Parameters:
    epsilon (array-like): The sampled noise array of shape (D,).
    epsilon_theta (array-like): The model prediction array of shape (D,).
    sigma (array-like): The diagonal covariance matrix represented as a 1D array of shape (D,).

    Returns:
    float: The PriorGrad weighted loss value.
    """
    epsilon = np.asarray(epsilon, dtype=float)
    epsilon_theta = np.asarray(epsilon_theta, dtype=float)
    sigma = np.asarray(sigma, dtype=float)

    # Compute the difference between epsilon and epsilon_theta
    diff = epsilon - epsilon_theta

    # Compute the weighted squared norm
    loss = np.sum((diff ** 2) / sigma)

    return float(loss)
