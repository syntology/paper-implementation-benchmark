import numpy as np


def langevin_step(y_t, grad_f_theta, epsilon_t, delta):
    """
    Compute one step of Langevin dynamics for Discrete Walk-Jump Sampling.
    
    Args:
        y_t: Current state, shape (d,)
        grad_f_theta: Gradient of energy function at y_t, shape (d,)
        epsilon_t: Standard normal random sample, shape (d,)
        delta: Step size (scalar)
    
    Returns:
        y_{t+1}: Next state, shape (d,)
    """
    y_t = np.asarray(y_t, dtype=float)
    grad_f_theta = np.asarray(grad_f_theta, dtype=float)
    epsilon_t = np.asarray(epsilon_t, dtype=float)
    delta = float(delta)
    
    # Langevin dynamics update: y_{t+1} = y_t - delta * grad_f_theta + sqrt(2 * delta) * epsilon_t
    y_next = y_t - delta * grad_f_theta + np.sqrt(2 * delta) * epsilon_t
    
    return y_next
