import numpy as np


def project_onto_euclidean_ball(theta, theta_star, delta):
    """
    Project parameter vector theta onto the Euclidean ball centered at theta_star
    with radius delta.
    
    Args:
        theta: 1D numpy array of shape (d,) - parameter vector to project
        theta_star: 1D numpy array of shape (d,) - center of the Euclidean ball
        delta: positive scalar - radius of the Euclidean ball
    
    Returns:
        1D numpy array of shape (d,) - projected parameter vector
    """
    # Convert inputs to numpy arrays with float dtype
    theta = np.asarray(theta, dtype=float)
    theta_star = np.asarray(theta_star, dtype=float)
    delta = float(delta)
    
    # Compute the difference vector
    diff = theta - theta_star
    
    # Compute the Euclidean distance (L2 norm)
    dist = np.linalg.norm(diff)
    
    # If theta is already within the ball, return it unchanged
    if dist <= delta:
        return theta
    
    # Otherwise, project onto the boundary of the ball
    # theta_star + delta * (theta - theta_star) / dist
    projected = theta_star + delta * diff / dist
    
    return projected
