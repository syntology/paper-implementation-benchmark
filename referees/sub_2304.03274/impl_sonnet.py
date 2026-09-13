import numpy as np


def compute_diffmimic_loss(states, reference_states):
    """
    Compute the DiffMimic loss as the sum of squared L2 distances between
    predicted states and reference states across all timesteps.
    
    Args:
        states: Array of shape (T, D) containing predicted states
        reference_states: Array of shape (T, D) containing reference states
    
    Returns:
        float: Scalar loss L = sum_{t=0}^{T-1} ||s_t - ŝ_t||_2^2
    
    Raises:
        ValueError: If shapes of states and reference_states don't match
    """
    # Convert inputs to numpy arrays with float dtype
    states = np.asarray(states, dtype=float)
    reference_states = np.asarray(reference_states, dtype=float)
    
    # Check that shapes match
    if states.shape != reference_states.shape:
        raise ValueError(
            f"Shape mismatch: states has shape {states.shape} but "
            f"reference_states has shape {reference_states.shape}"
        )
    
    # Compute difference between states and reference states
    diff = states - reference_states
    
    # Compute squared L2 norm for each timestep: ||s_t - ŝ_t||_2^2
    # This is the sum of squared differences across all dimensions for each timestep
    squared_norms = np.sum(diff ** 2, axis=1)
    
    # Sum across all timesteps to get total loss
    loss = np.sum(squared_norms)
    
    # Return as Python float
    return float(loss)
