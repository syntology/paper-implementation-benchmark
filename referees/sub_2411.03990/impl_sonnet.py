import numpy as np
from scipy.linalg import logm, expm


def se3_diffusion_step(H_k, H_hat_k_to_0, lambda_0, lambda_1):
    """
    Compute a single SE(3) diffusion denoising step for a trajectory of poses.
    
    Args:
        H_k: Array of shape (T_p+1, 4, 4) representing poses at diffusion step k
        H_hat_k_to_0: Array of shape (T_p+1, 4, 4) representing predicted clean poses
        lambda_0: Scalar float weight for the predicted update
        lambda_1: Scalar float weight for the current pose
    
    Returns:
        H_k_minus_1: Array of shape (T_p+1, 4, 4) representing poses at step k-1
    """
    # Convert inputs to numpy arrays
    H_k = np.asarray(H_k, dtype=float)
    H_hat_k_to_0 = np.asarray(H_hat_k_to_0, dtype=float)
    lambda_0 = float(lambda_0)
    lambda_1 = float(lambda_1)
    
    # Get the number of poses
    T_p_plus_1 = H_k.shape[0]
    
    # Initialize output array
    H_k_minus_1 = np.zeros_like(H_k)
    
    # Process each pose in the trajectory
    for i in range(T_p_plus_1):
        # (1) Compute M_i = H_hat_k_to_0[i] @ H_k[i]
        M_i = H_hat_k_to_0[i] @ H_k[i]
        
        # (2) Compute log_M_i = Log(M_i) using matrix logarithm
        log_M_i = logm(M_i)
        
        # (3) Compute log_H_i = Log(H_k[i])
        log_H_i = logm(H_k[i])
        
        # (4) Compute combined = lambda_0 * log_M_i + lambda_1 * log_H_i
        combined = lambda_0 * log_M_i + lambda_1 * log_H_i
        
        # (5) Compute H_k_minus_1[i] = Exp(combined) using matrix exponential
        H_k_minus_1[i] = expm(combined)
    
    return H_k_minus_1
