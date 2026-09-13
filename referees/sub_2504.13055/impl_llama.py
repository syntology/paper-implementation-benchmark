import numpy as np

def compute_advantages(rewards):
    """
    Compute advantages by subtracting the mean of rewards from each reward,
    then dividing by the standard deviation of rewards.

    Args:
        rewards (np.ndarray): A 1D array of shape (n,) containing scalar rewards for each rollout.

    Returns:
        np.ndarray: A 1D array of shape (n,) containing advantages for each rollout.
    """
    mean_rewards = np.mean(rewards)
    std_rewards = np.std(rewards, ddof=1)
    advantages = (rewards - mean_rewards) / std_rewards
    return advantages

def compute_ppo_clipped_objective(log_probs_current, log_probs_old, rewards, epsilon):
    """
    Compute the PPO clipped objective function for a batch of rollouts.

    Args:
        log_probs_current (np.ndarray): A 1D array of shape (n,) containing log probabilities of n rollouts under the current policy.
        log_probs_old (np.ndarray): A 1D array of shape (n,) containing log probabilities of the same n rollouts under the old policy.
        rewards (np.ndarray): A 1D array of shape (n,) containing scalar rewards for each rollout.
        epsilon (float): A scalar clipping parameter.

    Returns:
        float: The mean of the PPO clipped objective function values for the batch of rollouts.
    """
    log_probs_current = np.asarray(log_probs_current, dtype=float)
    log_probs_old = np.asarray(log_probs_old, dtype=float)
    rewards = np.asarray(rewards, dtype=float)

    advantages = compute_advantages(rewards)
    probability_ratios = np.exp(log_probs_current - log_probs_old)
    clipped_ratios = np.clip(probability_ratios, 1 - epsilon, 1 + epsilon)
    objective_values = np.minimum(probability_ratios * advantages, clipped_ratios * advantages)
    objective = np.mean(objective_values)
    return float(objective)
