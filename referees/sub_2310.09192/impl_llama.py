import numpy as np

def compute_structure_loss(A_c, A_c_prime):
    """
    Compute the structure loss between a real graph adjacency matrix A_c and a synthetic graph adjacency matrix A_c_prime.

    Args:
    A_c (numpy array): The real graph adjacency matrix with float values in [0, 1].
    A_c_prime (numpy array): The synthetic graph adjacency matrix with float values in [0, 1].

    Returns:
    float: The mean squared error between the two adjacency matrices.
    """
    A_c = np.asarray(A_c, dtype=float)
    A_c_prime = np.asarray(A_c_prime, dtype=float)

    # Get the minimum size of the two matrices
    min_size = min(A_c.shape[0], A_c_prime.shape[0])
    min_size = min(min_size, A_c.shape[1], A_c_prime.shape[1])

    # If either matrix is empty or min_size is 0, return 0.0
    if min_size == 0:
        return 0.0

    # Compute the mean squared error only on the minimum overlapping region
    mse = np.mean((A_c[:min_size, :min_size] - A_c_prime[:min_size, :min_size]) ** 2)

    return float(mse)
