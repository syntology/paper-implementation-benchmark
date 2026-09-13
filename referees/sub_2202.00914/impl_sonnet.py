import numpy as np


def compute_lsd_reward(phi_s_t, phi_s_t_plus_1, z):
    """
    Compute the Lipschitz-constrained Skill Discovery (LSD) reward.
    
    The reward is defined as: r^LSD(s_t, a_t, s_{t+1}) = (phi(s_{t+1}) - phi(s_t))^T * z
    
    Args:
        phi_s_t: 1D numpy array of shape (d,) representing the feature representation 
                 of the current state
        phi_s_t_plus_1: 1D numpy array of shape (d,) representing the feature representation 
                        of the next state
        z: 1D numpy array of shape (d,) representing the skill vector
    
    Returns:
        float: The scalar reward value
    """
    # Convert inputs to numpy arrays with float dtype
    phi_s_t = np.asarray(phi_s_t, dtype=float)
    phi_s_t_plus_1 = np.asarray(phi_s_t_plus_1, dtype=float)
    z = np.asarray(z, dtype=float)
    
    # Compute the difference vector: delta = phi(s_{t+1}) - phi(s_t)
    delta = phi_s_t_plus_1 - phi_s_t
    
    # Compute the dot product: reward = delta^T * z
    reward = np.dot(delta, z)
    
    # Return as plain Python float
    return float(reward)
