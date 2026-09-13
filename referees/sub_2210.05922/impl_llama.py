import numpy as np

def compute_model_importance_weight(q_values_real, q_values_model, alpha):
    """
    Compute the Model Importance Weight (MIW) omega(s,a) as described in Eq. (dr_target_final) of the AMPL paper.

    Parameters:
    q_values_real (numpy array): Q-values estimated on real data.
    q_values_model (numpy array): Q-values estimated on model-generated data.
    alpha (float): A positive scalar that controls the temperature/scale of the exponential weighting.

    Returns:
    omega (numpy array): A 1D numpy array of shape (N,) containing the importance weights omega(s,a) for each state-action pair.
    """
    q_values_real = np.asarray(q_values_real, dtype=float)
    q_values_model = np.asarray(q_values_model, dtype=float)
    alpha = float(alpha)
    
    # Compute the difference between Q-values estimated on real data and model-generated data
    q_diff = q_values_real - q_values_model
    
    # Compute the importance weight as exp(alpha * (q_values_real - q_values_model))
    omega = np.exp(alpha * q_diff)
    
    return omega
