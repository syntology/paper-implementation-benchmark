import numpy as np


def linear_transform_and_clip(x_prime, W, B, epsilon):
    """
    Apply per-class linear transformation with clipping as described in Learnability Lock.
    
    Args:
        x_prime: Input data sample of shape (d,) where d is the feature dimension
        W: Weight matrix of shape (C, d) where C is the number of classes
        B: Bias matrix of shape (C, d)
        epsilon: Scalar perturbation bound
        
    Returns:
        Array of shape (C, d) where row c contains the transformed sample for class c
    """
    # Convert inputs to numpy arrays with float dtype
    x_prime = np.asarray(x_prime, dtype=float)
    W = np.asarray(W, dtype=float)
    B = np.asarray(B, dtype=float)
    epsilon = float(epsilon)
    
    # Step 1: Clip W element-wise to [1 - epsilon/2, 1 + epsilon/2]
    W_clipped = np.clip(W, 1 - epsilon / 2, 1 + epsilon / 2)
    
    # Step 2: Clip B element-wise to [-epsilon/2, +epsilon/2]
    B_clipped = np.clip(B, -epsilon / 2, epsilon / 2)
    
    # Step 3 & 4: For each class c, compute transformed_c = W[c, :] * x_prime + B[c, :]
    # Broadcasting: x_prime has shape (d,), W_clipped has shape (C, d)
    # W_clipped * x_prime broadcasts to (C, d) with element-wise multiplication
    transformed = W_clipped * x_prime + B_clipped
    
    # Ensure output is float64
    return transformed.astype(np.float64)
