import numpy as np

def polyak_average_update(target_params, online_params, rho):
    """
    Performs Polyak averaging (exponential moving average) update for target network parameters.

    Args:
    target_params (numpy array): Target parameters.
    online_params (numpy array): Online parameters.
    rho (float): Momentum coefficient.

    Returns:
    numpy array: Updated target parameters.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    target_params = np.asarray(target_params, dtype=float)
    online_params = np.asarray(online_params, dtype=float)

    # Check if rho is a scalar float in [0, 1]
    assert isinstance(rho, (int, float)) and 0 <= rho <= 1, "rho must be a scalar float in [0, 1]"

    # Check if target_params and online_params have matching shapes
    assert target_params.shape == online_params.shape, "target_params and online_params must have matching shapes"

    # Compute the updated target parameters using Polyak averaging
    updated_target_params = rho * target_params + (1 - rho) * online_params

    return updated_target_params
