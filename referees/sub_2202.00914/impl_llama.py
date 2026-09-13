import numpy as np

def compute_lsd_reward(phi_s_t, phi_s_t_plus_1, z):
    """
    Compute the Lipschitz-constrained Skill Discovery (LSD) reward.

    Parameters:
    phi_s_t (array-like): The feature representation of the current state.
    phi_s_t_plus_1 (array-like): The feature representation of the next state.
    z (array-like): The skill vector.

    Returns:
    float: The LSD reward value.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    phi_s_t = np.asarray(phi_s_t, dtype=float)
    phi_s_t_plus_1 = np.asarray(phi_s_t_plus_1, dtype=float)
    z = np.asarray(z, dtype=float)

    # Check if all arrays have the same dimensionality
    assert phi_s_t.shape == phi_s_t_plus_1.shape == z.shape, "All arrays must have the same dimensionality"

    # Compute the difference vector
    delta = phi_s_t_plus_1 - phi_s_t

    # Compute the dot product
    reward = np.dot(delta, z)

    # Return the scalar reward
    return float(reward)
