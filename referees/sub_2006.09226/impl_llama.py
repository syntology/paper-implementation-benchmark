import numpy as np

def pbvf_critic_loss(q_values, rewards, next_q_values, gamma):
    """
    Compute the mean squared TD error loss for the PBVF critic.

    Args:
    q_values (array-like): Q(s, a, θ̃) for each transition in the batch.
    rewards (array-like): Immediate reward r for each transition.
    next_q_values (array-like): Q(s', a'~π_θ̃(s'), θ̃) for each transition.
    gamma (float): Discount factor in [0, 1].

    Returns:
    float: Mean squared TD error loss.
    """
    q_values = np.asarray(q_values, dtype=float)
    rewards = np.asarray(rewards, dtype=float)
    next_q_values = np.asarray(next_q_values, dtype=float)

    # Compute TD target
    td_targets = rewards + gamma * next_q_values

    # Compute TD error
    td_errors = q_values - td_targets

    # Compute mean squared TD error loss
    loss = np.mean(td_errors ** 2)

    return float(loss)
