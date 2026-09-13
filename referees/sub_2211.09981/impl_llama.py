import numpy as np

def ensemble_loss(log_ps, log_pt, strategy):
    """
    Compute the weighted ensemble self-supervised learning loss given student and teacher log probabilities across multiple ensemble heads.

    Args:
    log_ps (numpy array): Student log probabilities of shape (b, n, c).
    log_pt (numpy array): Teacher log probabilities of shape (b, n, c).
    strategy (str): One of 'mean', 'entropy_weighted', or 'max'.

    Returns:
    float: The computed loss value.
    """
    log_ps = np.asarray(log_ps, dtype=float)
    log_pt = np.asarray(log_pt, dtype=float)

    if strategy == 'mean':
        return _mean_strategy(log_ps, log_pt)
    elif strategy == 'entropy_weighted':
        return _entropy_weighted_strategy(log_ps, log_pt)
    elif strategy == 'max':
        return _max_strategy(log_ps, log_pt)
    else:
        raise ValueError("Invalid strategy. Must be one of 'mean', 'entropy_weighted', or 'max'.")

def _mean_strategy(log_ps, log_pt):
    """
    Compute cross-entropy loss between student and teacher for each (batch_sample, ensemble_head) pair and average over all batch samples and ensemble heads.

    Args:
    log_ps (numpy array): Student log probabilities of shape (b, n, c).
    log_pt (numpy array): Teacher log probabilities of shape (b, n, c).

    Returns:
    float: The computed loss value.
    """
    b, n, c = log_ps.shape
    pt = np.exp(log_pt)
    loss = -np.sum(pt * log_ps, axis=-1)  # (b, n)
    return np.mean(loss)

def _entropy_weighted_strategy(log_ps, log_pt):
    """
    Compute entropy weighted loss.

    Args:
    log_ps (numpy array): Student log probabilities of shape (b, n, c).
    log_pt (numpy array): Teacher log probabilities of shape (b, n, c).

    Returns:
    float: The computed loss value.
    """
    b, n, c = log_ps.shape
    pt = np.exp(log_pt)
    tau_ent = 0.04
    entropies = -np.mean(np.sum(pt * log_pt, axis=-1), axis=0)  # (n,)
    weights = np.exp(entropies / tau_ent)  # (n,)
    weights /= np.sum(weights)
    per_head_loss = -np.mean(np.sum(pt * log_ps, axis=-1), axis=0)  # (n,)
    return np.sum(weights * per_head_loss)

def _max_strategy(log_ps, log_pt):
    """
    Compute loss only for the ensemble head that maximizes max_over_c(log_pt[i,j,c]) for each batch sample.

    Args:
    log_ps (numpy array): Student log probabilities of shape (b, n, c).
    log_pt (numpy array): Teacher log probabilities of shape (b, n, c).

    Returns:
    float: The computed loss value.
    """
    b, n, c = log_ps.shape
    pt = np.exp(log_pt)
    max_pt = np.max(log_pt, axis=-1)  # (b, n)
    max_head = np.argmax(max_pt, axis=-1)  # (b,)
    loss = -np.sum(pt[np.arange(b), :, :] * log_ps[np.arange(b), :, :], axis=-1)  # (b, n)
    loss = loss[np.arange(b), max_head]  # (b,)
    return np.mean(loss)
