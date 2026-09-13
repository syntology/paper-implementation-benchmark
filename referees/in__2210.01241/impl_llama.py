import numpy as np

def clip(x, lo, hi):
    """
    Clip a value to a specified range.

    Args:
    x (float): The value to clip.
    lo (float): The lower bound of the range.
    hi (float): The upper bound of the range.

    Returns:
    float: The clipped value.
    """
    return np.maximum(lo, np.minimum(x, hi))

def ppo_clip_objective(log_probs_new, log_probs_old, advantages, epsilon):
    """
    Compute the PPO-Clip objective for a batch of timesteps.

    Args:
    log_probs_new (array-like): Log probabilities of actions under the current policy.
    log_probs_old (array-like): Log probabilities of the same actions under the old policy.
    advantages (array-like): Advantage estimates.
    epsilon (float): The clipping parameter.

    Returns:
    float: The mean of the surrogate losses over all timesteps.
    """
    log_probs_new = np.asarray(log_probs_new, dtype=float)
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    advantages = np.asarray(advantages, dtype=float)

    # Compute the probability ratios
    ratios = np.exp(log_probs_new - log_probs_old)

    # Compute the clipped ratios
    clipped_ratios = clip(ratios, 1 - epsilon, 1 + epsilon)

    # Compute the surrogate losses
    surrogate_losses = np.minimum(ratios * advantages, clipped_ratios * advantages)

    # Return the mean of the surrogate losses
    return float(np.mean(surrogate_losses))
