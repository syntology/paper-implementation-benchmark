import numpy as np

def dual_variable_update(lambda_t, eta, constraint_value, b_prime, U, epsilon):
    """
    Compute the dual variable update for constrained MDP optimization.

    Parameters:
    lambda_t (float): Current dual variable.
    eta (float): Step size.
    constraint_value (float): Empirical constraint value.
    b_prime (float): Constraint RHS.
    U (float): Projection upper bound.
    epsilon (float): Epsilon-net resolution.

    Returns:
    float: Updated dual variable.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    lambda_t = np.asarray(lambda_t, dtype=float)
    eta = np.asarray(eta, dtype=float)
    constraint_value = np.asarray(constraint_value, dtype=float)
    b_prime = np.asarray(b_prime, dtype=float)
    U = np.asarray(U, dtype=float)
    epsilon = np.asarray(epsilon, dtype=float)

    # Compute gradient step
    temp = lambda_t - eta * (constraint_value - b_prime)

    # Project temp onto [0, U]
    clipped = np.maximum(0, np.minimum(temp, U))

    # Round clipped to nearest epsilon-net point
    lambda_next = epsilon * np.round(clipped / epsilon)

    # Return the updated dual variable as a plain Python float
    return float(lambda_next)
