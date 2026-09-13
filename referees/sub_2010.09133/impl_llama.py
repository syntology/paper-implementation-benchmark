import numpy as np

def matrix_power(A, n):
    """
    Compute the matrix power A^n using standard matrix exponentiation.
    
    Parameters:
    A (numpy array): The input matrix.
    n (int): The exponent.
    
    Returns:
    numpy array: The result of A^n.
    """
    if n == 0:
        return np.eye(A.shape[0])
    elif n % 2 == 0:
        half_pow = matrix_power(A, n // 2)
        return np.dot(half_pow, half_pow)
    else:
        half_pow = matrix_power(A, n // 2)
        return np.dot(np.dot(half_pow, half_pow), A)

def gradient_acyclicity_constraint(W):
    """
    Compute the gradient of the acyclicity constraint h(W) with respect to the weighted adjacency matrix W.
    
    Parameters:
    W (numpy array): The input weighted adjacency matrix.
    
    Returns:
    numpy array: The gradient ∇h(W).
    """
    W = np.asarray(W, dtype=float)
    d = W.shape[0]
    alpha = 1 / d
    I = np.eye(d)
    temp_matrix = matrix_power(I + alpha * np.multiply(W, W), d - 1)
    gradient = alpha * np.dot(temp_matrix.T, 2 * W)
    return gradient
