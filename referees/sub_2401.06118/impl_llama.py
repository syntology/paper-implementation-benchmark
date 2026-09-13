import numpy as np

def aqlm_reconstruction_loss(X_gram, W, C, b, s):
    """
    Compute the AQLM reconstruction loss for a single linear layer.

    Parameters:
    X_gram (array-like): (n_in, n_in) Gram matrix X @ X^T where X is the layer input
    W (array-like): (n_out, n_in) weight matrix to be quantized
    C (array-like): (n_codebooks, codebook_size, n_out, n_in) tensor of codebook entries
    b (array-like): (n_out, n_in, n_codebooks) integer array of codebook indices, each in [0, codebook_size)
    s (array-like): (n_out, n_in, n_codebooks) float array of scaling factors

    Returns:
    float: The AQLM reconstruction loss
    """
    X_gram = np.asarray(X_gram, dtype=float)
    W = np.asarray(W, dtype=float)
    C = np.asarray(C, dtype=float)
    b = np.asarray(b, dtype=int)
    s = np.asarray(s, dtype=float)

    # Reconstruct the quantized weight W_hat
    W_hat = reconstruct_weight(W.shape, C, b, s)

    # Compute the squared Frobenius norm loss weighted by the input Gram matrix
    loss = compute_loss(W, W_hat, X_gram)

    return loss


def reconstruct_weight(shape, C, b, s):
    """
    Reconstruct the quantized weight W_hat.

    Parameters:
    shape (tuple): The shape of the weight matrix
    C (array-like): (n_codebooks, codebook_size, n_out, n_in) tensor of codebook entries
    b (array-like): (n_out, n_in, n_codebooks) integer array of codebook indices, each in [0, codebook_size)
    s (array-like): (n_out, n_in, n_codebooks) float array of scaling factors

    Returns:
    array-like: The reconstructed quantized weight W_hat
    """
    n_out, n_in = shape
    n_codebooks = C.shape[0]
    W_hat = np.zeros((n_out, n_in))

    for i in range(n_out):
        for j in range(n_in):
            for k in range(n_codebooks):
                W_hat[i, j] += s[i, j, k] * C[k, b[i, j, k], i, j]

    return W_hat


def compute_loss(W, W_hat, X_gram):
    """
    Compute the squared Frobenius norm loss weighted by the input Gram matrix.

    Parameters:
    W (array-like): The original weight matrix
    W_hat (array-like): The reconstructed quantized weight matrix
    X_gram (array-like): The input Gram matrix

    Returns:
    float: The squared Frobenius norm loss
    """
    diff = W_hat - W
    loss = np.trace(diff @ X_gram @ diff.T)

    return loss
