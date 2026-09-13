import numpy as np


def gamma_mve_q_loss(q_current, reward, gamma_v, v_mve_next):
    """
    Compute the temporal difference loss for the Q-function update in the
    γ-model based value expansion algorithm.
    
    This implements the loss function from Algorithm 1 (γ-model based value expansion):
    L = 0.5 * (Q(s,a) - (r + γ_v * V_γ-MVE(s')))^2
    
    Args:
        q_current: Current Q-value prediction Q_ω(s,a). Scalar or 1D array of shape (N,).
        reward: Immediate reward r(s,a). Scalar or 1D array of shape (N,).
        gamma_v: Value discount factor γ_v ∈ [0,1]. Scalar.
        v_mve_next: γ-MVE value estimate of next state V_γ-MVE(s'). 
                    Scalar or 1D array of shape (N,).
    
    Returns:
        float: Mean squared TD error averaged across all samples.
    """
    # Convert inputs to numpy arrays with float dtype
    q_current = np.asarray(q_current, dtype=float)
    reward = np.asarray(reward, dtype=float)
    gamma_v = np.asarray(gamma_v, dtype=float)
    v_mve_next = np.asarray(v_mve_next, dtype=float)
    
    # Compute TD target: r + γ_v * V_γ-MVE(s')
    td_target = reward + gamma_v * v_mve_next
    
    # Compute TD error: Q(s,a) - (r + γ_v * V_γ-MVE(s'))
    td_error = q_current - td_target
    
    # Compute mean squared TD error: 0.5 * mean((td_error)^2)
    loss = 0.5 * np.mean(td_error ** 2)
    
    # Return as plain Python float
    return float(loss)
