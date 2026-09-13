import numpy as np

def favor_plus_attention(Q_prime, K_prime, V, is_bidirectional):
    """
    Compute FAVOR+ attention mechanism from the Performers paper.
    
    Args:
        Q_prime: array of shape (L, M) - transformed queries
        K_prime: array of shape (L, M) - transformed keys
        V: array of shape (L, d) - values
        is_bidirectional: boolean flag for bidirectional vs causal attention
    
    Returns:
        array of shape (L, d) - attention output
    """
    Q_prime = np.asarray(Q_prime, dtype=float)
    K_prime = np.asarray(K_prime, dtype=float)
    V = np.asarray(V, dtype=float)
    
    L = Q_prime.shape[0]
    d = V.shape[1]
    
    # Form C by concatenating V with a column of ones
    ones_column = np.ones((L, 1), dtype=float)
    C = np.concatenate([V, ones_column], axis=1)  # Shape (L, d+1)
    
    if is_bidirectional:
        # Bidirectional attention
        # Buf_1 = (K_prime)^T @ C
        Buf_1 = K_prime.T @ C  # Shape (M, d+1)
        # Buf_2 = Q_prime @ Buf_1
        Buf_2 = Q_prime @ Buf_1  # Shape (L, d+1)
    else:
        # Unidirectional (causal) attention
        M = K_prime.shape[1]
        Buf_2 = np.zeros((L, d + 1), dtype=float)
        
        # Compute cumulative sum of outer products
        G = np.zeros((M, d + 1), dtype=float)
        for i in range(L):
            # G_i = sum_{j=0}^{i} outer_product(K_prime[j, :], C[j, :])
            # outer_product(K_prime[j, :], C[j, :]) = K_prime[j, :, None] @ C[j, None, :]
            G += np.outer(K_prime[i, :], C[i, :])  # Accumulate
            # Buf_2[i, :] = Q_prime[i, :] @ G_i
            Buf_2[i, :] = Q_prime[i, :] @ G
    
    # Split Buf_2 into Buf_3 (first d columns) and buf_4 (last column)
    Buf_3 = Buf_2[:, :d]  # Shape (L, d)
    buf_4 = Buf_2[:, d]   # Shape (L,)
    
    # Return Buf_3 with each row divided by corresponding buf_4 element
    result = Buf_3 / buf_4[:, np.newaxis]  # Shape (L, d)
    
    return result
