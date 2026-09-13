import numpy as np


def voice2series_loss(log_probs, target_labels):
    """
    Compute the Voice2Series cross-entropy loss.
    
    Args:
        log_probs: 2D array of shape (n, C) containing log probabilities
                   log P(class|input) for each sample and class
        target_labels: 1D integer array of shape (n,) containing true class labels
                      with values in range [0, C-1]
    
    Returns:
        Scalar float representing the average negative log-likelihood
    """
    # Convert inputs to numpy arrays
    log_probs = np.asarray(log_probs, dtype=float)
    target_labels = np.asarray(target_labels, dtype=np.int64)
    
    # Get number of samples
    n = log_probs.shape[0]
    
    # Compute loss: L = -(1/n) * sum_{i=0}^{n-1} log_probs[i, target_labels[i]]
    # Extract log probabilities for the true labels
    selected_log_probs = log_probs[np.arange(n), target_labels]
    
    # Compute average negative log-likelihood
    loss = -np.mean(selected_log_probs)
    
    # Return as plain Python float
    return float(loss)
