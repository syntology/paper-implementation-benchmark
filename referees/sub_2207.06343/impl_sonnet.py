import numpy as np


def compute_entk_features(x, phi_B, omega_r, mask):
    """
    Compute empirical Neural Tangent Kernel (eNTK) features for a single input.
    
    Args:
        x: Input array of shape (D,) - not used in this computation as phi_B is pre-computed
        phi_B: 1D array of shape (E,) - output of bootstrapped feature extractor applied to x
        omega_r: 2D array of shape (C, E) - randomly re-initialized linear layer weights
        mask: 1D boolean array of shape (E,) - sub-sampling mask over feature parameters
    
    Returns:
        masked_grad: 1D array of shape (E,) - masked gradient (eNTK features)
    """
    # Convert inputs to numpy arrays with float dtype
    phi_B = np.asarray(phi_B, dtype=float)
    omega_r = np.asarray(omega_r, dtype=float)
    mask = np.asarray(mask, dtype=float)
    
    # Step 1: Compute the first logit
    # logit_1 = omega_r[0, :] @ phi_B
    # This is the dot product of the first row of omega_r with phi_B
    logit_1 = np.dot(omega_r[0, :], phi_B)
    
    # Step 2: Compute gradient of logit_1 with respect to phi_B
    # Since logit_1 = sum_i(omega_r[0, i] * phi_B[i])
    # d(logit_1)/d(phi_B[i]) = omega_r[0, i]
    # So the gradient is simply the first row of omega_r
    gradient = omega_r[0, :]
    
    # Step 3: Apply the mask element-wise
    masked_grad = gradient * mask
    
    # Step 4: Return the masked gradient
    return masked_grad
