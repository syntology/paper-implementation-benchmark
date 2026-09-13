import numpy as np

def project_delta_to_l2_ball(delta, c_delta):
    """
    Projects a perturbation vector delta onto an L2 ball of radius c_delta.

    Args:
    delta (numpy array): A 1D numpy array of shape (d,) representing the perturbation vector.
    c_delta (float): A positive scalar representing the L2 norm bound.

    Returns:
    numpy array: A 1D numpy array of shape (d,) with the projected perturbation.
    """
    delta = np.asarray(delta, dtype=float)
    l2_norm = np.linalg.norm(delta)
    scaling_factor = min(1, c_delta / l2_norm)
    return delta * scaling_factor

# Helper function to calculate the L2 norm
def calculate_l2_norm(delta):
    """
    Calculates the L2 norm of a vector.

    Args:
    delta (numpy array): A 1D numpy array of shape (d,) representing the vector.

    Returns:
    float: The L2 norm of the vector.
    """
    return np.sqrt(np.sum(delta**2))

# Alternative implementation using the helper function
def project_delta_to_l2_ball_alternative(delta, c_delta):
    """
    Projects a perturbation vector delta onto an L2 ball of radius c_delta.

    Args:
    delta (numpy array): A 1D numpy array of shape (d,) representing the perturbation vector.
    c_delta (float): A positive scalar representing the L2 norm bound.

    Returns:
    numpy array: A 1D numpy array of shape (d,) with the projected perturbation.
    """
    delta = np.asarray(delta, dtype=float)
    l2_norm = calculate_l2_norm(delta)
    scaling_factor = min(1, c_delta / l2_norm)
    return delta * scaling_factor
