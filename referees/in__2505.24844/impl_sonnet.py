import numpy as np


def compute_chameleon_domain_weights(K, lambda_reg, mode):
    """
    Compute CHAMELEON domain weights from a domain affinity matrix.
    
    Args:
        K: (k, k) numpy array, the domain affinity matrix
        lambda_reg: float, regularization parameter λ > 0
        mode: string, either 'pretrain' or 'finetune'
    
    Returns:
        alpha: (k,) numpy array of domain weights, summing to 1.0
    """
    # Convert inputs to numpy arrays with appropriate dtype
    K = np.asarray(K, dtype=float)
    lambda_reg = float(lambda_reg)
    
    # Get number of domains
    k = K.shape[0]
    
    # Step 1: Compute KRLS scores S_λ(D_i) for each domain i
    # S_λ(D_i) = K[i,i] - K[i,:] @ inv(K + λ*I) @ K[:,i]
    
    # Create identity matrix
    I = np.eye(k)
    
    # Compute K + λ*I
    K_reg = K + lambda_reg * I
    
    # Compute inverse of (K + λ*I)
    K_reg_inv = np.linalg.inv(K_reg)
    
    # Compute KRLS scores for all domains
    S_lambda = np.zeros(k, dtype=float)
    for i in range(k):
        # S_λ(D_i) = K[i,i] - K[i,:] @ K_reg_inv @ K[:,i]
        S_lambda[i] = K[i, i] - K[i, :] @ K_reg_inv @ K[:, i]
    
    # Step 2: Compute raw scores based on mode
    if mode == 'pretrain':
        # For pretraining: use inverse of KRLS scores
        raw_scores = 1.0 / S_lambda
    elif mode == 'finetune':
        # For finetuning: use direct KRLS scores
        raw_scores = S_lambda
    else:
        raise ValueError(f"mode must be 'pretrain' or 'finetune', got '{mode}'")
    
    # Step 3: Apply numerically stable softmax
    # Subtract max for numerical stability
    raw_scores_shifted = raw_scores - np.max(raw_scores)
    exp_scores = np.exp(raw_scores_shifted)
    alpha = exp_scores / np.sum(exp_scores)
    
    return alpha
