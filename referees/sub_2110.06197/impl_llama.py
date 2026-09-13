import numpy as np

def back_to_cell(X, L):
    """
    Apply periodic boundary conditions to fractional coordinates.

    Parameters:
    X (np.ndarray): Fractional coordinates (N, 3)
    L (np.ndarray): Lattice matrix (3, 3)

    Returns:
    np.ndarray: Wrapped fractional coordinates (N, 3)
    """
    # Compute Cartesian position
    cart = X @ L
    
    # Convert back to fractional
    LT = L.T
    f = np.linalg.solve(LT, cart.T).T
    
    # Wrap into [0,1)^3
    f_wrapped = f - np.floor(f)
    
    return f_wrapped

def langevin_coordinate_update(X_prev, score, alpha, epsilon_noise, L):
    """
    Perform one Langevin dynamics update step for fractional coordinates.

    Parameters:
    X_prev (array-like): Previous fractional coordinates (N, 3)
    score (array-like): Predicted score (gradient) for each atom (N, 3)
    alpha (float): Scalar step size
    epsilon_noise (array-like): Pre-drawn standard normal samples (N, 3)
    L (array-like): Lattice matrix (3, 3)

    Returns:
    np.ndarray: Updated fractional coordinates (N, 3)
    """
    # Convert array-like arguments to numpy arrays
    X_prev = np.asarray(X_prev, dtype=float)
    score = np.asarray(score, dtype=float)
    epsilon_noise = np.asarray(epsilon_noise, dtype=float)
    L = np.asarray(L, dtype=float)

    # Update rule
    X_prime = X_prev + alpha * score + np.sqrt(2 * alpha) * epsilon_noise
    
    # Apply back_to_cell
    X_updated = back_to_cell(X_prime, L)
    
    return X_updated
