import numpy as np


def ppo_clip_objective(log_probs_new, log_probs_old, advantages, epsilon):
    """
    Compute the PPO-Clip objective for a batch of timesteps.
    
    Args:
        log_probs_new: 1D array of shape (N,) containing log probabilities 
                       of actions under the current policy
        log_probs_old: 1D array of shape (N,) containing log probabilities 
                       of the same actions under the old policy
        advantages: 1D array of shape (N,) containing advantage estimates
        epsilon: scalar clipping parameter
    
    Returns:
        Mean of surrogate losses over all N timesteps as a scalar float
    """
    # Convert inputs to numpy arrays with float dtype
    log_probs_new = np.asarray(log_probs_new, dtype=float)
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    advantages = np.asarray(advantages, dtype=float)
    epsilon = float(epsilon)
    
    # Compute probability ratio: r_i = exp(log_probs_new[i] - log_probs_old[i])
    ratio = np.exp(log_probs_new - log_probs_old)
    
    # Compute clipped ratio: clip(r_i, 1-epsilon, 1+epsilon)
    clipped_ratio = np.clip(ratio, 1.0 - epsilon, 1.0 + epsilon)
    
    # Compute surrogate losses for each timestep
    # surrogate_i = min(r_i * advantages[i], clipped_r_i * advantages[i])
    surrogate_unclipped = ratio * advantages
    surrogate_clipped = clipped_ratio * advantages
    surrogate_loss = np.minimum(surrogate_unclipped, surrogate_clipped)
    
    # Return the mean of surrogate losses as a scalar float
    return float(np.mean(surrogate_loss))
