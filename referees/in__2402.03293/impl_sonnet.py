import numpy as np

def flora_momentum_update(M_t, G_t, A_current, A_next, beta, is_reseed_step):
    """
    Compute the FLORA momentum update for a single weight matrix.
    
    Args:
        M_t: Current momentum state, shape (n, r)
        G_t: Current gradient, shape (n, m)
        A_current: Current random matrix, shape (r, m)
        A_next: Next random matrix, shape (r, m)
        beta: Momentum decay rate, scalar in [0, 1]
        is_reseed_step: Boolean indicating whether this is a reseeding step
        
    Returns:
        M_next: Updated momentum state, shape (n, r)
    """
    # Convert inputs to numpy arrays with float dtype
    M_t = np.asarray(M_t, dtype=float)
    G_t = np.asarray(G_t, dtype=float)
    A_current = np.asarray(A_current, dtype=float)
    A_next = np.asarray(A_next, dtype=float)
    beta = float(beta)
    
    # Compute M_prime based on whether this is a reseeding step
    if is_reseed_step:
        # M_prime = M_t @ A_current @ A_next.T
        M_prime = M_t @ A_current @ A_next.T
    else:
        # M_prime = M_t
        M_prime = M_t
    
    # Compute M_next = beta * M_prime + (1 - beta) * G_t @ A_next.T
    M_next = beta * M_prime + (1 - beta) * G_t @ A_next.T
    
    return M_next
