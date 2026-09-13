import numpy as np


def compute_model_importance_weight(q_values_real, q_values_model, alpha):
    """
    Compute the Model Importance Weight (MIW) omega(s,a) for AMPL algorithm.
    
    The MIW is used to reweight the model training objective based on the
    difference between Q-values estimated on real data versus model-generated data.
    
    Args:
        q_values_real: 1D array of shape (N,) containing Q-values for N state-action
                      pairs from the real environment dataset
        q_values_model: 1D array of shape (N,) containing Q-values for the same N
                       state-action pairs evaluated on model-generated rollouts
        alpha: Positive scalar float controlling the temperature/scale of the
              exponential weighting
    
    Returns:
        1D numpy array of shape (N,) containing the importance weights omega(s,a)
        for each state-action pair
    """
    # Convert inputs to numpy arrays with float dtype
    q_values_real = np.asarray(q_values_real, dtype=float)
    q_values_model = np.asarray(q_values_model, dtype=float)
    alpha = float(alpha)
    
    # Compute the Q-value difference
    q_diff = q_values_real - q_values_model
    
    # Compute importance weights: omega(s,a) = exp(alpha * (Q_real - Q_model))
    omega = np.exp(alpha * q_diff)
    
    return omega
