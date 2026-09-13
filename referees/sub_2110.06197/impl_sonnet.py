import numpy as np

def langevin_coordinate_update(X_prev, score, alpha, epsilon_noise, L):
    """
    Performs one Langevin dynamics update step for fractional coordinates in a periodic crystal cell.
    
    Args:
        X_prev: shape (N, 3) fractional coordinates of N atoms
        score: shape (N, 3) predicted score (gradient) for each atom
        alpha: scalar step size
        epsilon_noise: shape (N, 3) pre-drawn standard normal samples
        L: shape (3, 3) lattice matrix where rows are lattice vectors
    
    Returns:
        X_wrapped: shape (N, 3) wrapped fractional coordinates in [0, 1)^3
    """
    # Convert inputs to numpy arrays with float dtype
    X_prev = np.asarray(X_prev, dtype=float)
    score = np.asarray(score, dtype=float)
    alpha = float(alpha)
    epsilon_noise = np.asarray(epsilon_noise, dtype=float)
    L = np.asarray(L, dtype=float)
    
    # Langevin dynamics update (Algorithm line 11)
    X_prime = X_prev + alpha * score + np.sqrt(2 * alpha) * epsilon_noise
    
    # Apply back_to_cell operation (Algorithm line 12)
    X_wrapped = back_to_cell(X_prime, L)
    
    return X_wrapped

def back_to_cell(X_frac, L):
    """
    Wraps fractional coordinates back into the unit cell [0, 1)^3.
    
    Args:
        X_frac: shape (N, 3) fractional coordinates
        L: shape (3, 3) lattice matrix where rows are lattice vectors
    
    Returns:
        X_wrapped: shape (N, 3) wrapped fractional coordinates in [0, 1)^3
    """
    N = X_frac.shape[0]
    
    # Convert fractional to Cartesian coordinates
    # X_frac[i] @ L gives Cartesian position (row vector times matrix)
    cart = X_frac @ L  # shape (N, 3)
    
    # Convert Cartesian back to fractional coordinates
    # Solve L^T @ f^T = cart^T for each atom
    # Equivalently: f = cart @ inv(L^T) = cart @ inv(L).T
    L_T = L.T  # shape (3, 3)
    
    # Solve for fractional coordinates
    # For each atom i: L^T @ f[i] = cart[i]
    frac = np.linalg.solve(L_T, cart.T).T  # shape (N, 3)
    
    # Wrap into [0, 1)^3 using periodic boundary conditions
    frac_wrapped = frac - np.floor(frac)
    
    return frac_wrapped
