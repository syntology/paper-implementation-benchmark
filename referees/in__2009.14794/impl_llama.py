import numpy as np

def favor_plus_attention(Q_prime, K_prime, V, is_bidirectional):
    """
    Compute the FAVOR+ attention mechanism as described in the Performers paper.

    Parameters:
    Q_prime (array-like): Transformed queries of shape (L, M)
    K_prime (array-like): Transformed keys of shape (L, M)
    V (array-like): Values of shape (L, d)
    is_bidirectional (bool): Flag for bidirectional or unidirectional attention

    Returns:
    array-like: Attention output of shape (L, d)
    """
    Q_prime = np.asarray(Q_prime, dtype=float)
    K_prime = np.asarray(K_prime, dtype=float)
    V = np.asarray(V, dtype=float)

    # Form C by horizontally concatenating V with a column vector of ones of length L
    C = np.concatenate((V, np.ones((V.shape[0], 1))), axis=1)

    if is_bidirectional:
        # Compute Buf_1 = (K_prime)^T @ C
        Buf_1 = K_prime.T @ C
        # Compute Buf_2 = Q_prime @ Buf_1
        Buf_2 = Q_prime @ Buf_1
    else:
        # Initialize Buf_2
        Buf_2 = np.zeros((Q_prime.shape[0], C.shape[1]))
        # Compute unidirectional (causal) attention
        for i in range(Q_prime.shape[0]):
            G_i = np.sum([np.outer(K_prime[j, :], C[j, :]) for j in range(i + 1)], axis=0)
            Buf_2[i, :] = Q_prime[i, :] @ G_i

    # Split Buf_2 into Buf_3 (first d columns) and buf_4 (last column)
    Buf_3 = Buf_2[:, :-1]
    buf_4 = Buf_2[:, -1]

    # Return Buf_3 with each row i divided by buf_4[i]
    return Buf_3 / buf_4[:, np.newaxis]
