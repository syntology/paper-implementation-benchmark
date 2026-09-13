import numpy as np

def dual_variable_update(lambda_t, eta, constraint_value, b_prime, U, epsilon):
    """
    Compute the dual variable update for constrained MDP optimization.
    
    Implements the update rule from Algorithm 1 (arXiv:2206.06270):
    lambda_{t+1} = R_Lambda[P_{[0,U]}[lambda_t - eta * (constraint_value - b_prime)]]
    
    where:
    - P_{[0,U]} is projection onto [0, U]
    - R_Lambda is rounding to nearest epsilon-net point in {0, epsilon, 2*epsilon, ..., U}
    
    Args:
        lambda_t: Current dual variable (scalar)
        eta: Step size (scalar, positive)
        constraint_value: Empirical constraint value (scalar)
        b_prime: Constraint RHS (scalar)
        U: Projection upper bound (scalar, non-negative)
        epsilon: Epsilon-net resolution (scalar, positive)
    
    Returns:
        lambda_{t+1}: Updated dual variable (scalar float)
    """
    # Convert inputs to float
    lambda_t = float(np.asarray(lambda_t, dtype=float))
    eta = float(np.asarray(eta, dtype=float))
    constraint_value = float(np.asarray(constraint_value, dtype=float))
    b_prime = float(np.asarray(b_prime, dtype=float))
    U = float(np.asarray(U, dtype=float))
    epsilon = float(np.asarray(epsilon, dtype=float))
    
    # Step 1: Gradient step
    temp = lambda_t - eta * (constraint_value - b_prime)
    
    # Step 2: Project onto [0, U]
    clipped = max(0.0, min(temp, U))
    
    # Step 3: Round to nearest epsilon-net point
    # The epsilon-net is {0, epsilon, 2*epsilon, ..., U}
    # Round clipped/epsilon to nearest integer, then multiply by epsilon
    lambda_next = epsilon * np.round(clipped / epsilon)
    
    # Ensure the result stays within [0, U] after rounding (due to numerical precision)
    lambda_next = max(0.0, min(lambda_next, U))
    
    return float(lambda_next)
