import numpy as np

def polyak_average_update(target_params, online_params, rho):
    """
    Performs Polyak averaging (exponential moving average) update for target network parameters.
    
    Implements the update rule from Diffusion Q-learning:
    target_params_new = rho * target_params + (1 - rho) * online_params
    
    Args:
        target_params: Current target network parameters (array-like)
        online_params: Current online network parameters (array-like)
        rho: Momentum coefficient, scalar float in [0, 1]
    
    Returns:
        Updated target parameters as numpy array with same shape as inputs
    """
    target_params = np.asarray(target_params, dtype=float)
    online_params = np.asarray(online_params, dtype=float)
    rho = float(rho)
    
    # Polyak averaging: θ' = ρ * θ' + (1 - ρ) * θ
    target_params_new = rho * target_params + (1 - rho) * online_params
    
    return target_params_new
