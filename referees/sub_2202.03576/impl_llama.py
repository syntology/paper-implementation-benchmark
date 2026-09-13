import numpy as np

def clip_weights(W, epsilon):
    """
    Clip W element-wise to [1 - epsilon/2, 1 + epsilon/2].
    
    Parameters:
    W (numpy array): Weight matrix of shape (C, d) where C is the number of classes.
    epsilon (float): Perturbation bound.
    
    Returns:
    numpy array: Clipped weight matrix.
    """
    return np.clip(W, 1 - epsilon/2, 1 + epsilon/2)

def clip_biases(B, epsilon):
    """
    Clip B element-wise to [-epsilon/2, +epsilon/2].
    
    Parameters:
    B (numpy array): Bias matrix of shape (C, d) where C is the number of classes.
    epsilon (float): Perturbation bound.
    
    Returns:
    numpy array: Clipped bias matrix.
    """
    return np.clip(B, -epsilon/2, +epsilon/2)

def linear_transform(x_prime, W, B):
    """
    For each class c in 0..C-1, compute transformed_c = W[c, :] * x_prime + B[c, :].
    
    Parameters:
    x_prime (numpy array): Single data sample of shape (d,).
    W (numpy array): Weight matrix of shape (C, d) where C is the number of classes.
    B (numpy array): Bias matrix of shape (C, d) where C is the number of classes.
    
    Returns:
    numpy array: Array of shape (C, d) where row c contains the transformed sample for class c.
    """
    return W * x_prime + B

def linear_transform_and_clip(x_prime, W, B, epsilon):
    """
    Apply per-class linear transformation with clipping as described in Learnability Lock algorithm.
    
    Parameters:
    x_prime (array-like): Single data sample of shape (d,).
    W (array-like): Weight matrix of shape (C, d) where C is the number of classes.
    B (array-like): Bias matrix of shape (C, d) where C is the number of classes.
    epsilon (float): Perturbation bound.
    
    Returns:
    numpy array: Array of shape (C, d) where row c contains the transformed sample for class c.
    """
    x_prime = np.asarray(x_prime, dtype=float)
    W = np.asarray(W, dtype=float)
    B = np.asarray(B, dtype=float)
    
    W_clipped = clip_weights(W, epsilon)
    B_clipped = clip_biases(B, epsilon)
    
    return linear_transform(x_prime, W_clipped, B_clipped)
