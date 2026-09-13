import numpy as np

def compute_optimal_shift_up(membrane_potentials, spikes, theta, epsilon):
    """
    Compute the optimal upward shift for initial membrane potential according to the algorithm's upward shift rule.

    Parameters:
    membrane_potentials (1D array of length rho): membrane potentials at each time step
    spikes (1D array of length rho with values 0 or 1): spikes at each time step
    theta (scalar): threshold
    epsilon (scalar): shifting variable

    Returns:
    float: the shift amount to be added to the initial membrane potential
    """
    membrane_potentials = np.asarray(membrane_potentials, dtype=float)
    spikes = np.asarray(spikes, dtype=float)

    # Get the membrane potentials where the spike is 0
    membrane_potentials_no_spike = membrane_potentials[spikes == 0]

    # If there are no time steps where spike is 0, return theta
    if len(membrane_potentials_no_spike) == 0:
        return float(theta)

    # Compute the maximum membrane potential among all time steps where the spike is 0
    max_v = np.max(membrane_potentials_no_spike)

    # Compute the shift amount
    shift_amount = max(theta, theta + epsilon - max_v)

    return float(shift_amount)
