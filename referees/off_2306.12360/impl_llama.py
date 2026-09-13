import numpy as np

def langevin_step(y_t, grad_f_theta, epsilon_t, delta):
    """
    Compute one step of Langevin dynamics for the Walk-Jump sampling algorithm.

    Parameters:
    y_t (array-like): The current state.
    grad_f_theta (array-like): The gradient of the energy function at y_t.
    epsilon_t (array-like): A standard normal random sample.
    delta (scalar): The step size.

    Returns:
    y_{t+1} (numpy array): The next state.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    y_t = np.asarray(y_t, dtype=float)
    grad_f_theta = np.asarray(grad_f_theta, dtype=float)
    epsilon_t = np.asarray(epsilon_t, dtype=float)

    # Compute y_{t+1} using the Langevin dynamics formula
    y_t_plus_1 = y_t - delta * grad_f_theta + np.sqrt(2 * delta) * epsilon_t

    return y_t_plus_1
