import numpy as np


def ppo_clip_objective_gradient_step(log_probs_old, log_probs_new, advantages, epsilon):
    """
    Compute the PPO-Clip objective function value for a batch of experiences.
    
    This implements the PPO-Clip objective J_PPO(theta) from the DACT paper,
    which is to be maximized during gradient ascent.
    
    Args:
        log_probs_old: 1D numpy array of shape (N,) containing log probabilities
                       of actions under the old policy pi_old
        log_probs_new: 1D numpy array of shape (N,) containing log probabilities
                       of the same actions under the current policy pi_theta
        advantages: 1D numpy array of shape (N,) containing advantage estimates
                    A_hat for each time step
        epsilon: scalar float clipping threshold (varepsilon in the paper)
    
    Returns:
        scalar float: mean of the element-wise minimum of surrogate objectives
    """
    # Convert inputs to numpy arrays with float dtype
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    log_probs_new = np.asarray(log_probs_new, dtype=float)
    advantages = np.asarray(advantages, dtype=float)
    epsilon = float(epsilon)
    
    # Compute probability ratio: ratio_i = exp(log_probs_new[i] - log_probs_old[i])
    ratio = np.exp(log_probs_new - log_probs_old)
    
    # Compute clipped ratio: clip(ratio_i, 1-epsilon, 1+epsilon)
    clipped_ratio = np.clip(ratio, 1.0 - epsilon, 1.0 + epsilon)
    
    # Compute surrogate objectives
    surrogate1 = ratio * advantages
    surrogate2 = clipped_ratio * advantages
    
    # Take element-wise minimum
    surrogate_min = np.minimum(surrogate1, surrogate2)
    
    # Return mean over all samples as a scalar float
    return float(np.mean(surrogate_min))
