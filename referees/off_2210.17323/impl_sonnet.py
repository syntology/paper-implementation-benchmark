import numpy as np

def gptq_quantize_weight_matrix(W, H_inv, B, quant_min, quant_max):
    """
    Quantize weight matrix W using GPTQ algorithm.
    
    Args:
        W: Weight matrix of shape (d_row, d_col)
        H_inv: Inverse Hessian matrix of shape (d_col, d_col), symmetric positive definite
        B: Block size (positive integer dividing d_col)
        quant_min: Minimum quantization value
        quant_max: Maximum quantization value
    
    Returns:
        Q: Quantized weight matrix of shape (d_row, d_col) as float64 array
    """
    # Convert inputs to numpy arrays
    W = np.asarray(W, dtype=float)
    H_inv = np.asarray(H_inv, dtype=float)
    
    d_row, d_col = W.shape
    
    # Initialize Q (quantized output) and E (block quantization errors)
    Q = np.zeros((d_row, d_col), dtype=np.float64)
    E = np.zeros((d_row, B), dtype=np.float64)
    
    # Compute Cholesky decomposition of H_inv (upper triangular)
    H_inv_chol = np.linalg.cholesky(H_inv).T
    
    # Make a working copy of W since we modify it in-place
    W = W.copy()
    
    # Iterate over column blocks
    for block_start in range(0, d_col, B):
        # Process each column in the current block
        for j in range(block_start, block_start + B):
            # Quantize column j
            Q[:, j] = np.clip(np.round(W[:, j]), quant_min, quant_max)
            
            # Compute quantization error
            E[:, j - block_start] = (W[:, j] - Q[:, j]) / H_inv_chol[j, j]
            
            # Update weights in current block
            # outer product: E[:, j - block_start].reshape(-1, 1) @ H_inv_chol[j, j:(block_start + B)].reshape(1, -1)
            error_col = E[:, j - block_start].reshape(-1, 1)
            hessian_row = H_inv_chol[j, j:(block_start + B)].reshape(1, -1)
            W[:, j:(block_start + B)] -= error_col @ hessian_row
        
        # Update all remaining weights after processing the block
        if block_start + B < d_col:
            W[:, (block_start + B):] -= E @ H_inv_chol[block_start:(block_start + B), (block_start + B):]
    
    return Q
