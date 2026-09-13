import numpy as np


def compute_recipient_policy_gradient_update(log_probs, rewards, incentives, baseline, learning_rate):
    """
    Compute the policy gradient update for a reward-recipient agent in the LIO framework.
    
    Args:
        log_probs: array of shape (T,) containing log probabilities of actions taken
        rewards: array of shape (T,) containing environmental rewards at each timestep
        incentives: array of shape (T,) containing incentive rewards from other agents
        baseline: scalar float, baseline value for variance reduction
        learning_rate: scalar float, step size for gradient ascent
    
    Returns:
        delta_theta: scalar float representing the policy parameter update magnitude
    """
    # Convert inputs to numpy arrays with float dtype
    log_probs = np.asarray(log_probs, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    incentives = np.asarray(incentives, dtype=float)
    baseline = float(baseline)
    learning_rate = float(learning_rate)
    
    # Step 1: Compute total rewards at each timestep
    total_rewards = rewards + incentives
    
    # Step 2: Compute returns using cumulative sum from end to start
    # returns[t] = sum(total_rewards[k] for k in t..T-1)
    # This is equivalent to reverse cumulative sum
    returns = np.cumsum(total_rewards[::-1])[::-1]
    
    # Step 3: Compute advantages
    advantages = returns - baseline
    
    # Step 4: Compute gradient
    grad = np.sum(log_probs * advantages)
    
    # Step 5: Compute parameter update
    delta_theta = learning_rate * grad
    
    return float(delta_theta)
