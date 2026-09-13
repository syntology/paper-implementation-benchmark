import numpy as np
from scipy.linalg import logm, expm

def se3_diffusion_step(H_k, H_hat_k_to_0, lambda_0, lambda_1):
    """
    Compute a single SE(3) diffusion denoising step for a trajectory of poses.

    Parameters:
    H_k (array-like): Array of shape (T_p+1, 4, 4) representing T_p+1 homogeneous transformation matrices at diffusion step k.
    H_hat_k_to_0 (array-like): Array of shape (T_p+1, 4, 4) representing the predicted clean poses.
    lambda_0 (float): Scalar float.
    lambda_1 (float): Scalar float.

    Returns:
    H_k_minus_1 (array): Array of shape (T_p+1, 4, 4) representing the denoised poses.
    """
    H_k = np.asarray(H_k, dtype=float)
    H_hat_k_to_0 = np.asarray(H_hat_k_to_0, dtype=float)

    def se3_log(H):
        """
        Compute the matrix logarithm in se(3) Lie algebra.

        Parameters:
        H (array-like): 4x4 homogeneous transformation matrix.

        Returns:
        log_H (array): 4x4 skew-symmetric matrix + translation block.
        """
        log_H = logm(H)
        return log_H

    def se3_exp(log_H):
        """
        Compute the matrix exponential mapping se(3) back to SE(3).

        Parameters:
        log_H (array-like): 4x4 skew-symmetric matrix + translation block.

        Returns:
        H (array): 4x4 homogeneous transformation matrix.
        """
        H = expm(log_H)
        return H

    T_p = H_k.shape[0] - 1
    H_k_minus_1 = np.zeros_like(H_k)

    for i in range(T_p + 1):
        M_i = np.dot(H_hat_k_to_0[i], H_k[i])
        log_M_i = se3_log(M_i)
        log_H_i = se3_log(H_k[i])
        combined = lambda_0 * log_M_i + lambda_1 * log_H_i
        H_k_minus_1[i] = se3_exp(combined)

    return H_k_minus_1
