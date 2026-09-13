import numpy as np

def compute_recipient_policy_gradient_update(log_probs, rewards, incentives, baseline, learning_rate):
    """
    Compute the policy gradient update for a reward-recipient agent in the LIO framework.

    Parameters:
    log_probs (array-like): log probabilities of actions taken in a trajectory
    rewards (array-like): environmental rewards at each timestep
    incentives (array-like): incentive rewards received from other agents at each timestep
    baseline (float): baseline value subtracted from returns for variance reduction
    learning_rate (float): step size for the gradient ascent update

    Returns:
    float: policy parameter update magnitude
    """
    log_probs = np.asarray(log_probs, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    incentives = np.asarray(incentives, dtype=float)

    total_rewards = rewards + incentives
    returns = np.cumsum(total_rewards[::-1])[::-1]
    advantages = returns - baseline
    grad = np.sum(log_probs * advantages)
    delta_theta = learning_rate * grad

    return float(delta_theta)
