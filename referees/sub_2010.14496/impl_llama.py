import numpy as np

def gamma_mve_q_loss(q_current, reward, gamma_v, v_mve_next):
    """
    Compute the temporal difference loss for the Q-function update in the γ-model based value expansion algorithm.

    Args:
    q_current (scalar or 1D array of shape (N,)): The current Q-value prediction.
    reward (scalar or 1D array of shape (N,)): The immediate reward.
    gamma_v (scalar in [0,1]): The value discount factor.
    v_mve_next (scalar or 1D array of shape (N,)): The γ-MVE value estimate of the next state.

    Returns:
    A scalar float representing the average loss across all samples.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    q_current = np.asarray(q_current, dtype=float)
    reward = np.asarray(reward, dtype=float)
    gamma_v = np.asarray(gamma_v, dtype=float)
    v_mve_next = np.asarray(v_mve_next, dtype=float)

    # Compute the target Q-value
    target_q = reward + gamma_v * v_mve_next

    # Compute the temporal difference error
    td_error = q_current - target_q

    # Compute the mean squared TD error
    loss = 0.5 * np.mean(td_error ** 2)

    # Return the loss as a plain Python float
    return float(loss)
