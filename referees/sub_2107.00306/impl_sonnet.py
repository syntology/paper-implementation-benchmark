import numpy as np


def model_based_next_state_prediction(s_t, a_t, delta_pred):
    """
    Compute the next state s_{t+1} using the learned dynamics model prediction.
    
    The dynamics model m(s_t, a_t) outputs a delta (change) that is added to 
    the current state, following the algorithm line:
    s'_{t+j+1} = s'_{t+j} + m(s'_{t+j}, a'_{t+j})
    
    Args:
        s_t: 1D numpy array of shape (state_dim,) representing the current state
        a_t: 1D numpy array of shape (action_dim,) representing the action taken
        delta_pred: 1D numpy array of shape (state_dim,) representing the 
                    predicted state change from the dynamics model m(s_t, a_t)
    
    Returns:
        s_{t+1}: 1D numpy array of shape (state_dim,) representing the predicted next state
    """
    # Convert inputs to numpy arrays with float dtype
    s_t = np.asarray(s_t, dtype=float)
    a_t = np.asarray(a_t, dtype=float)
    delta_pred = np.asarray(delta_pred, dtype=float)
    
    # Compute next state: s_{t+1} = s_t + delta_pred (element-wise addition)
    s_t_plus_1 = s_t + delta_pred
    
    return s_t_plus_1
