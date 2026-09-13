import numpy as np

def compute_bootstrap_deviation(v_resampled, v_subset):
    """
    Compute the bootstrap deviation epsilon for a single bootstrap iteration in the Bootstrapping FQE algorithm.

    Parameters:
    v_resampled (float): A scalar value estimate computed on a resampled dataset.
    v_subset (float): A scalar value estimate computed on the original subset.

    Returns:
    float: The difference between v_resampled and v_subset.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    v_resampled = np.asarray(v_resampled, dtype=float)
    v_subset = np.asarray(v_subset, dtype=float)

    # Ensure inputs are scalar
    assert v_resampled.shape == () and v_subset.shape == (), "Inputs must be scalar"

    # Compute the bootstrap deviation epsilon
    epsilon = v_resampled - v_subset

    # Return the result as a plain Python float
    return float(epsilon)
