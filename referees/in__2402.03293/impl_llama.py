import numpy as np

def matrix_multiply(A, B):
    """
    Compute the matrix product of A and B.
    
    Parameters:
    A (np.ndarray): The first matrix.
    B (np.ndarray): The second matrix.
    
    Returns:
    np.ndarray: The matrix product of A and B.
    """
    return np.matmul(A, B)

def flora_momentum_update(M_t, G_t, A_current, A_next, beta, is_reseed_step):
    """
    Compute the FLORA momentum update for a single weight matrix at timestep t.
    
    Parameters:
    M_t (array-like): The current momentum state (shape n×r).
    G_t (array-like): The current gradient (shape n×m).
    A_current (array-like): The current random matrix (shape r×m).
    A_next (array-like): The next random matrix (shape r×m).
    beta (float): The momentum decay rate (scalar in [0,1]).
    is_reseed_step (bool): Whether this is a reseeding step (t ≡ 0 mod κ).
    
    Returns:
    np.ndarray: The updated momentum state (shape n×r).
    """
    M_t = np.asarray(M_t, dtype=float)
    G_t = np.asarray(G_t, dtype=float)
    A_current = np.asarray(A_current, dtype=float)
    A_next = np.asarray(A_next, dtype=float)
    
    if is_reseed_step:
        M_prime = matrix_multiply(matrix_multiply(M_t, A_current), A_next.T)
    else:
        M_prime = M_t
    
    M_next = beta * M_prime + (1 - beta) * matrix_multiply(G_t, A_next.T)
    
    return M_next
