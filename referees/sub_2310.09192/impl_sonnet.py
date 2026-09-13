import numpy as np


def compute_structure_loss(A_c, A_c_prime):
    """
    Compute the structure loss L_structure between real and synthetic graph adjacency matrices.
    
    Uses mean squared error (MSE) between adjacency matrices, which is the standard
    structure matching loss in graph distillation literature.
    
    Args:
        A_c: Real graph adjacency matrix of shape (N, N) with float values in [0, 1]
        A_c_prime: Synthetic graph adjacency matrix of shape (N', N') with float values in [0, 1]
    
    Returns:
        Scalar float representing the MSE between the overlapping regions of the matrices.
        If sizes differ, only the top-left min(N, N') x min(N, N') region is compared.
        Returns 0.0 if either matrix is empty or min_size is 0.
    """
    # Convert inputs to numpy arrays with float dtype
    A_c = np.asarray(A_c, dtype=float)
    A_c_prime = np.asarray(A_c_prime, dtype=float)
    
    # Handle empty matrices or invalid shapes
    if A_c.size == 0 or A_c_prime.size == 0:
        return 0.0
    
    if A_c.ndim != 2 or A_c_prime.ndim != 2:
        return 0.0
    
    # Get dimensions
    N = A_c.shape[0]
    N_prime = A_c_prime.shape[0]
    
    # Compute minimum size for overlapping region
    min_size = min(N, N_prime)
    
    # Handle edge case where min_size is 0
    if min_size == 0:
        return 0.0
    
    # Extract overlapping top-left regions
    A_c_overlap = A_c[:min_size, :min_size]
    A_c_prime_overlap = A_c_prime[:min_size, :min_size]
    
    # Compute mean squared error
    squared_diff = (A_c_overlap - A_c_prime_overlap) ** 2
    mse = np.sum(squared_diff) / (min_size * min_size)
    
    # Return as plain Python float
    return float(mse)
