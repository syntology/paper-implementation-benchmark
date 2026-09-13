import numpy as np

def compute_ratio(log_probs_old, log_probs_new):
    """
    Compute the ratio of new policy probabilities to old policy probabilities.
    
    Parameters:
    log_probs_old (numpy array): Log probabilities of actions under the old policy.
    log_probs_new (numpy array): Log probabilities of actions under the new policy.
    
    Returns:
    ratio (numpy array): Ratio of new policy probabilities to old policy probabilities.
    """
    return np.exp(log_probs_new - log_probs_old)

def clip_ratio(ratio, epsilon):
    """
    Clip the ratio to prevent large updates.
    
    Parameters:
    ratio (numpy array): Ratio of new policy probabilities to old policy probabilities.
    epsilon (float): Clipping threshold.
    
    Returns:
    clipped_ratio (numpy array): Clipped ratio.
    """
    return np.clip(ratio, 1 - epsilon, 1 + epsilon)

def compute_surrogate1(ratio, advantages):
    """
    Compute the first surrogate objective.
    
    Parameters:
    ratio (numpy array): Ratio of new policy probabilities to old policy probabilities.
    advantages (numpy array): Advantage estimates.
    
    Returns:
    surrogate1 (numpy array): First surrogate objective.
    """
    return ratio * advantages

def compute_surrogate2(clipped_ratio, advantages):
    """
    Compute the second surrogate objective.
    
    Parameters:
    clipped_ratio (numpy array): Clipped ratio.
    advantages (numpy array): Advantage estimates.
    
    Returns:
    surrogate2 (numpy array): Second surrogate objective.
    """
    return clipped_ratio * advantages

def compute_min_surrogate(surrogate1, surrogate2):
    """
    Compute the minimum of the two surrogate objectives.
    
    Parameters:
    surrogate1 (numpy array): First surrogate objective.
    surrogate2 (numpy array): Second surrogate objective.
    
    Returns:
    min_surrogate (numpy array): Minimum of the two surrogate objectives.
    """
    return np.minimum(surrogate1, surrogate2)

def ppo_clip_objective_gradient_step(log_probs_old, log_probs_new, advantages, epsilon):
    """
    Compute the PPO-Clip objective function value for a batch of experiences.
    
    Parameters:
    log_probs_old (numpy array): Log probabilities of actions under the old policy.
    log_probs_new (numpy array): Log probabilities of actions under the new policy.
    advantages (numpy array): Advantage estimates.
    epsilon (float): Clipping threshold.
    
    Returns:
    float: Mean of the minimum surrogate objectives.
    """
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    log_probs_new = np.asarray(log_probs_new, dtype=float)
    advantages = np.asarray(advantages, dtype=float)
    
    ratio = compute_ratio(log_probs_old, log_probs_new)
    clipped_ratio = clip_ratio(ratio, epsilon)
    surrogate1 = compute_surrogate1(ratio, advantages)
    surrogate2 = compute_surrogate2(clipped_ratio, advantages)
    min_surrogate = compute_min_surrogate(surrogate1, surrogate2)
    
    return np.mean(min_surrogate)
