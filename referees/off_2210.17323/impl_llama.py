import numpy as np

def cholesky(A, lower=False):
    """
    Compute the Cholesky decomposition of a symmetric positive definite matrix A.

    Args:
    A (np.ndarray): Symmetric positive definite matrix.
    lower (bool): Whether to return the lower triangular matrix. Defaults to False.

    Returns:
    np.ndarray: Upper triangular Cholesky decomposition of A if lower is False, otherwise lower triangular.
    """
    L = np.linalg.cholesky(A)
    if lower:
        return L
    else:
        return L.T

def gptq_quantize_weight_matrix(W, H_inv, B, quant_min, quant_max):
    """
    Quantize weight matrix W using GPTQ algorithm with inverse Hessian H_inv and blocksize B.

    Args:
    W (array-like): Weight matrix to be quantized.
    H_inv (array-like): Inverse Hessian matrix.
    B (int): Blocksize.
    quant_min (float): Minimum value of the quantization range.
    quant_max (float): Maximum value of the quantization range.

    Returns:
    np.ndarray: Quantized weight matrix.
    """
    W = np.asarray(W, dtype=float)
    H_inv = np.asarray(H_inv, dtype=float)

    # Initialize Q as zeros with shape (d_row, d_col)
    Q = np.zeros_like(W)

    # Initialize E as zeros with shape (d_row, B)
    E = np.zeros((W.shape[0], B))

    # Compute Cholesky decomposition of H_inv
    H_inv_chol = cholesky(H_inv, lower=False)

    # Iterate over column blocks
    for block_start in range(0, W.shape[1], B):
        # For each column j from block_start to block_start + B - 1 (inclusive)
        for j in range(block_start, min(block_start + B, W.shape[1])):
            # Quantize column
            Q[:, j] = np.clip(np.round(W[:, j]), quant_min, quant_max)

            # Compute error
            E[:, j - block_start] = (W[:, j] - Q[:, j]) / H_inv_chol[j, j]

            # Update weights in current block
            W[:, j:(block_start + B)] -= np.outer(E[:, j - block_start], H_inv_chol[j, j:(block_start + B)])

        # After processing all columns in block, update remaining weights
        if block_start + B < W.shape[1]:
            W[:, (block_start + B):] -= E @ H_inv_chol[block_start:(block_start + B), (block_start + B):]

    return Q.astype(np.float64)
