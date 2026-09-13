import numpy as np

def compute_entk_features(x, phi_B, omega_r, mask):
    """
    Compute empirical Neural Tangent Kernel (eNTK) features for a single input x.

    Parameters:
    x (array-like): Input of shape (D,).
    phi_B (array-like): Bootstrapped feature extractor output of shape (E,).
    omega_r (array-like): Randomly re-initialized linear layer weights of shape (C, E).
    mask (array-like): Sub-sampling mask over feature parameters of shape (E,).

    Returns:
    masked_grad (numpy.ndarray): Masked gradient of the first logit with respect to phi_B.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    x = np.asarray(x, dtype=float)
    phi_B = np.asarray(phi_B, dtype=float)
    omega_r = np.asarray(omega_r, dtype=float)
    mask = np.asarray(mask, dtype=float)

    # Compute the first logit
    logit_1 = np.dot(omega_r[0, :], phi_B)

    # Compute the gradient of logit_1 with respect to phi_B
    gradient = omega_r[0, :]

    # Apply the mask element-wise
    masked_grad = gradient * mask

    return masked_grad
