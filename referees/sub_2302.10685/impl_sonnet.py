import numpy as np


def compute_optimal_shift_up(membrane_potentials, spikes, theta, epsilon):
    """
    Compute the optimal upward shift for initial membrane potential.
    
    According to the algorithm's upward shift rule:
    shift = max(theta, theta + epsilon - max_v)
    where max_v is the maximum membrane potential among all time steps where spike is 0.
    
    Args:
        membrane_potentials: 1D array of membrane potentials at each time step (length rho)
        spikes: 1D array of spike values (0 or 1) at each time step (length rho)
        theta: threshold value (scalar)
        epsilon: shifting variable (scalar)
    
    Returns:
        float: The shift amount to be added to the initial membrane potential
    """
    # Convert inputs to numpy arrays with float dtype
    membrane_potentials = np.asarray(membrane_potentials, dtype=float)
    spikes = np.asarray(spikes, dtype=float)
    theta = float(theta)
    epsilon = float(epsilon)
    
    # Find indices where spike is 0
    no_spike_indices = spikes == 0
    
    # If there are no time steps where spike is 0, return theta
    if not np.any(no_spike_indices):
        return float(theta)
    
    # Get membrane potentials where spike is 0
    membrane_potentials_no_spike = membrane_potentials[no_spike_indices]
    
    # Find the maximum membrane potential among those time steps
    max_v = np.max(membrane_potentials_no_spike)
    
    # Compute the shift according to the formula:
    # max(theta, theta + epsilon - max_v)
    shift = max(theta, theta + epsilon - max_v)
    
    return float(shift)
