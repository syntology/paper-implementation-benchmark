import numpy as np

def compute_diffmimic_loss(states, reference_states):
    """
    Compute the DiffMimic loss as the sum of squared L2 distances between predicted states and reference states across all timesteps.

    Args:
    states (array-like): A 2D array of shape (T, D) where T is the number of timesteps and D is the state dimension.
    reference_states (array-like): A 2D array of shape (T, D) with the same dimensions.

    Returns:
    float: The scalar sum of the squared L2 norms across all T timesteps.

    Raises:
    ValueError: If the input arrays have mismatched shapes.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    states = np.asarray(states, dtype=float)
    reference_states = np.asarray(reference_states, dtype=float)

    # Check if the input arrays have identical shapes
    if states.shape != reference_states.shape:
        raise ValueError("Input arrays must have identical shapes")

    # Compute the squared L2 norm for each timestep
    squared_norms = np.sum((states - reference_states) ** 2, axis=1)

    # Compute the sum of the squared L2 norms across all timesteps
    loss = np.sum(squared_norms)

    # Return the result as a plain Python float
    return float(loss)
