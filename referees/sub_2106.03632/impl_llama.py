import numpy as np

def project_onto_euclidean_ball(theta, theta_star, delta):
    """
    Project parameter vector theta onto the Euclidean ball centered at theta_star with radius delta.

    Args:
    theta (numpy array): The input parameter vector.
    theta_star (numpy array): The center of the Euclidean ball.
    delta (float): The radius of the Euclidean ball.

    Returns:
    numpy array: The projected parameter vector.
    """
    theta = np.asarray(theta, dtype=float)
    theta_star = np.asarray(theta_star, dtype=float)
    delta = float(delta)

    # Compute the Euclidean distance between theta and theta_star
    dist = np.linalg.norm(theta - theta_star)

    # If the distance is less than or equal to delta, return theta unchanged
    if dist <= delta:
        return theta

    # If the distance is greater than delta, project theta onto the Euclidean ball
    return theta_star + delta * (theta - theta_star) / dist
