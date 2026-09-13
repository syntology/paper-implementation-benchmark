import numpy as np

def voice2series_loss(log_probs, target_labels):
    """
    Compute the Voice2Series cross-entropy loss.

    Parameters:
    log_probs (2D array): log probabilities log P(class|input) for each sample and class
    target_labels (1D array): true class labels for each sample

    Returns:
    float: average negative log-likelihood
    """
    log_probs = np.asarray(log_probs, dtype=float)
    target_labels = np.asarray(target_labels, dtype=int)
    
    # Get the number of samples
    n = log_probs.shape[0]
    
    # Compute the loss for each sample
    losses = log_probs[np.arange(n), target_labels]
    
    # Compute the average negative log-likelihood
    loss = -np.mean(losses)
    
    return float(loss)
