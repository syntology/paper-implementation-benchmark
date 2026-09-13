import numpy as np

def update_alpha_weights(alpha_current, grad_losses, eta_alpha):
    """
    Compute the updated alpha weights for the Common Good algorithm.

    Parameters:
    alpha_current (array-like): The current mixing weights (should sum to 1).
    grad_losses (array-like): The gradients of loss for each group with respect to model parameters theta.
    eta_alpha (float): The positive scalar step size.

    Returns:
    array: The normalized alpha weights.
    """
    alpha_current = np.asarray(alpha_current, dtype=float)
    grad_losses = np.asarray(grad_losses, dtype=float)
    eta_alpha = float(eta_alpha)

    # Compute the sum of all group gradients
    sum_grad = np.sum(grad_losses, axis=0)

    # Initialize the new alpha weights
    alpha_new = np.zeros_like(alpha_current)

    # For each group, compute the inner product and update the alpha weight
    for i in range(len(alpha_current)):
        inner_prod_i = np.dot(grad_losses[i], sum_grad)
        alpha_new[i] = alpha_current[i] * np.exp(eta_alpha * inner_prod_i)

    # Normalize the alpha weights
    alpha_new = alpha_new / np.sum(np.abs(alpha_new))

    return alpha_new
