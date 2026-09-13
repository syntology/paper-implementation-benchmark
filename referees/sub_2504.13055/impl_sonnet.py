import numpy as np


def compute_ppo_clipped_objective(log_probs_current, log_probs_old, rewards, epsilon):
    """
    Compute the PPO clipped objective function for a batch of rollouts.
    
    Args:
        log_probs_current: 1D array of shape (n,) containing log probabilities 
                          under current policy
        log_probs_old: 1D array of shape (n,) containing log probabilities 
                      under old policy
        rewards: 1D array of shape (n,) containing scalar rewards
        epsilon: scalar clipping parameter
    
    Returns:
        float: Mean of the clipped objective values
    """
    # Convert inputs to numpy arrays with float dtype
    log_probs_current = np.asarray(log_probs_current, dtype=float)
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    epsilon = float(epsilon)
    
    # Step 1: Compute advantages (normalized rewards)
    # advantages[i] = (rewards[i] - mean(rewards)) / std(rewards)
    mean_rewards = np.mean(rewards)
    std_rewards = np.std(rewards, ddof=1)  # Bessel's correction (divide by n-1)
    advantages = (rewards - mean_rewards) / std_rewards
    
    # Step 2: Compute probability ratios
    # ratio[i] = exp(log_probs_current[i] - log_probs_old[i])
    ratios = np.exp(log_probs_current - log_probs_old)
    
    # Step 3: Compute clipped ratios
    # clipped_ratio[i] = clip(ratio[i], 1-epsilon, 1+epsilon)
    clipped_ratios = np.clip(ratios, 1 - epsilon, 1 + epsilon)
    
    # Step 4: Compute the objective for each rollout
    # For each i, take min(ratio[i] * advantage[i], clipped_ratio[i] * advantage[i])
    unclipped_objective = ratios * advantages
    clipped_objective = clipped_ratios * advantages
    min_objective = np.minimum(unclipped_objective, clipped_objective)
    
    # Step 5: Return the mean as a scalar float
    return float(np.mean(min_objective))
