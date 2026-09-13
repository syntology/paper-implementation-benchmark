import numpy as np

def compute_krls_score(K, lambda_reg, i):
    """
    Compute the KRLS score S_λ(D_i) for a given domain i.

    Parameters:
    K (np.ndarray): Domain affinity matrix.
    lambda_reg (float): Regularization parameter λ.
    i (int): Domain index.

    Returns:
    float: KRLS score S_λ(D_i) for domain i.
    """
    k = K.shape[0]
    I = np.eye(k)
    inv_K = np.linalg.inv(K + lambda_reg * I)
    S_lambda = K[i, i] - K[i, :] @ inv_K @ K[:, i]
    return S_lambda

def compute_chameleon_domain_weights(K, lambda_reg, mode):
    """
    Compute CHAMELEON domain weights from a domain affinity matrix K.

    Parameters:
    K (np.ndarray): Domain affinity matrix.
    lambda_reg (float): Regularization parameter λ.
    mode (str): Either 'pretrain' or 'finetune'.

    Returns:
    np.ndarray: Domain weights α, summing to 1.0.
    """
    K = np.asarray(K, dtype=float)
    lambda_reg = float(lambda_reg)
    mode = str(mode)

    k = K.shape[0]
    S_lambda = np.array([compute_krls_score(K, lambda_reg, i) for i in range(k)])

    if mode == 'pretrain':
        raw_scores = 1.0 / S_lambda
    elif mode == 'finetune':
        raw_scores = S_lambda
    else:
        raise ValueError("Invalid mode. Must be either 'pretrain' or 'finetune'.")

    max_score = np.max(raw_scores)
    exp_scores = np.exp(raw_scores - max_score)
    alpha = exp_scores / np.sum(exp_scores)

    return alpha
