import numpy as np


def aqlm_reconstruction_loss(X_gram, W, C, b, s):
    """
    Compute the AQLM reconstruction loss for a single linear layer.
    
    Args:
        X_gram: (n_in, n_in) Gram matrix X @ X^T where X is the layer input
        W: (n_out, n_in) weight matrix to be quantized
        C: (n_codebooks, codebook_size, n_out, n_in) tensor of codebook entries
        b: (n_out, n_in, n_codebooks) integer array of codebook indices
        s: (n_out, n_in, n_codebooks) float array of scaling factors
    
    Returns:
        float: Loss = trace((W_hat - W) @ X_gram @ (W_hat - W)^T)
    """
    # Convert inputs to numpy arrays
    X_gram = np.asarray(X_gram, dtype=float)
    W = np.asarray(W, dtype=float)
    C = np.asarray(C, dtype=float)
    b = np.asarray(b, dtype=int)
    s = np.asarray(s, dtype=float)
    
    n_out, n_in = W.shape
    n_codebooks = C.shape[0]
    
    # Reconstruct W_hat from codebooks
    # W_hat[i, j] = sum_{k=0}^{n_codebooks-1} s[i, j, k] * C[k, b[i, j, k], i, j]
    W_hat = np.zeros((n_out, n_in), dtype=float)
    
    for i in range(n_out):
        for j in range(n_in):
            for k in range(n_codebooks):
                codebook_idx = b[i, j, k]
                W_hat[i, j] += s[i, j, k] * C[k, codebook_idx, i, j]
    
    # Compute the residual
    residual = W_hat - W
    
    # Compute loss = trace(residual @ X_gram @ residual^T)
    # This is equivalent to sum_{i,j} residual[i,:] @ X_gram @ residual[j,:]^T
    temp = residual @ X_gram  # (n_out, n_in)
    loss = np.trace(temp @ residual.T)  # scalar
    
    return float(loss)
