import numpy as np


def ensemble_loss(log_ps, log_pt, strategy):
    """
    Compute weighted ensemble self-supervised learning loss.
    
    Args:
        log_ps: numpy array of shape (b, n, c) containing student log probabilities
        log_pt: numpy array of shape (b, n, c) containing teacher log probabilities
        strategy: string, one of 'mean', 'entropy_weighted', or 'max'
    
    Returns:
        scalar float representing the loss value
    """
    log_ps = np.asarray(log_ps, dtype=float)
    log_pt = np.asarray(log_pt, dtype=float)
    
    b, n, c = log_ps.shape
    
    if strategy == 'mean':
        # Compute cross-entropy for each (batch_sample, ensemble_head) pair
        # CE = -sum_over_c(exp(log_pt[i,j,k]) * log_ps[i,j,k])
        pt = np.exp(log_pt)  # Convert to probabilities (b, n, c)
        ce = -np.sum(pt * log_ps, axis=2)  # (b, n)
        loss = np.mean(ce)
        return float(loss)
    
    elif strategy == 'entropy_weighted':
        tau_ent = 0.04
        
        # Compute entropy for each ensemble head
        # H_j = mean_over_batch(-sum_over_c(exp(log_pt[i,j,k]) * log_pt[i,j,k]))
        pt = np.exp(log_pt)  # (b, n, c)
        entropy_per_sample = -np.sum(pt * log_pt, axis=2)  # (b, n)
        H = np.mean(entropy_per_sample, axis=0)  # (n,)
        
        # Compute weights
        w = np.exp(H / tau_ent)  # (n,)
        w = w / np.sum(w)  # Normalize
        
        # Compute per-head loss
        # L_j = mean_over_batch(-sum_over_c(exp(log_pt[i,j,k]) * log_ps[i,j,k]))
        ce_per_sample = -np.sum(pt * log_ps, axis=2)  # (b, n)
        L = np.mean(ce_per_sample, axis=0)  # (n,)
        
        # Weighted sum
        loss = np.sum(w * L)
        return float(loss)
    
    elif strategy == 'max':
        # For each batch sample, find the ensemble head that maximizes max_over_c(log_pt[i,j,c])
        max_log_pt_per_head = np.max(log_pt, axis=2)  # (b, n)
        j_max = np.argmax(max_log_pt_per_head, axis=1)  # (b,)
        
        # Compute loss only for the selected head for each batch sample
        pt = np.exp(log_pt)  # (b, n, c)
        
        losses = []
        for i in range(b):
            j = j_max[i]
            # CE = -sum_over_c(exp(log_pt[i,j,k]) * log_ps[i,j,k])
            ce = -np.sum(pt[i, j, :] * log_ps[i, j, :])
            losses.append(ce)
        
        loss = np.mean(losses)
        return float(loss)
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
