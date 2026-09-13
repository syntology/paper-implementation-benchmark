import numpy as np


def pbvf_critic_loss(q_values, rewards, next_q_values, gamma):
    """
    Compute the mean squared TD error loss for the PBVF critic.
    
    Args:
        q_values: 1D array of shape (batch_size,) containing Q(s, a, θ̃)
        rewards: 1D array of shape (batch_size,) containing immediate rewards r
        next_q_values: 1D array of shape (batch_size,) containing Q(s', a'~π_θ̃(s'), θ̃)
        gamma: scalar discount factor in [0, 1]
    
    Returns:
        Mean squared TD error as a scalar float
    """
    # Convert inputs to numpy arrays with float dtype
    q_values = np.asarray(q_values, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    next_q_values = np.asarray(next_q_values, dtype=float)
    gamma = float(gamma)
    
    # Compute TD targets: y_i = r_i + gamma * Q(s', a', θ̃)
    td_targets = rewards + gamma * next_q_values
    
    # Compute TD errors: delta_i = Q(s, a, θ̃) - y_i
    td_errors = q_values - td_targets
    
    # Compute mean squared error: (1/batch_size) * sum(delta_i^2)
    mse_loss = np.mean(td_errors ** 2)
    
    # Return as plain Python float
    return float(mse_loss)
