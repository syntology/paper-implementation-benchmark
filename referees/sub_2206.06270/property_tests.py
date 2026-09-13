import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output is always in valid epsilon-net
    # Property: lambda_{t+1} must be a multiple of epsilon in [0, U]
    try:
        lambda_t = 0.5
        eta = 0.1
        constraint_value = 1.0
        b_prime = 0.8
        U = 2.0
        epsilon = 0.25
        
        result = fn(lambda_t, eta, constraint_value, b_prime, U, epsilon)
        
        # Check result is in [0, U]
        assert 0 <= result <= U, f"Result {result} outside [0, {U}]"
        
        # Check result is a multiple of epsilon (within floating point tolerance)
        remainder = result / epsilon - np.round(result / epsilon)
        assert abs(remainder) < 1e-6, f"Result {result} not a multiple of epsilon {epsilon}"
        
        results.append({
            "name": "output_in_valid_epsilon_net",
            "passed": True,
            "detail": f"Result {result} is valid epsilon-net point in [0, {U}]"
        })
    except Exception as e:
        results.append({
            "name": "output_in_valid_epsilon_net",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Boundary case - zero step size
    # Property: With eta=0, lambda_{t+1} should be lambda_t rounded to epsilon-net
    try:
        lambda_t = 0.37
        eta = 0.0
        constraint_value = 100.0
        b_prime = 50.0
        U = 1.0
        epsilon = 0.1
        
        result = fn(lambda_t, eta, constraint_value, b_prime, U, epsilon)
        expected = epsilon * np.round(lambda_t / epsilon)
        expected = np.clip(expected, 0, U)
        
        assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"
        
        results.append({
            "name": "zero_step_size_identity",
            "passed": True,
            "detail": f"With eta=0, result {result} equals rounded input {expected}"
        })
    except Exception as e:
        results.append({
            "name": "zero_step_size_identity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Constraint satisfied case
    # Property: When constraint_value == b_prime, gradient is zero, so result should be lambda_t rounded to epsilon-net
    try:
        lambda_t = 0.55
        eta = 0.2
        constraint_value = 0.75
        b_prime = 0.75
        U = 1.0
        epsilon = 0.1
        
        result = fn(lambda_t, eta, constraint_value, b_prime, U, epsilon)
        expected = epsilon * np.round(lambda_t / epsilon)
        expected = np.clip(expected, 0, U)
        
        assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"
        
        results.append({
            "name": "constraint_satisfied_no_update",
            "passed": True,
            "detail": f"When constraint satisfied, result {result} equals rounded input {expected}"
        })
    except Exception as e:
        results.append({
            "name": "constraint_satisfied_no_update",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Lower bound clipping
    # Property: Negative gradient step should be clipped to 0
    try:
        lambda_t = 0.05
        eta = 1.0
        constraint_value = 0.0
        b_prime = 1.0
        U = 2.0
        epsilon = 0.1
        
        result = fn(lambda_t, eta, constraint_value, b_prime, U, epsilon)
        
        # Gradient step: 0.05 - 1.0 * (0.0 - 1.0) = 0.05 + 1.0 = 1.05
        # After clipping to [0, 2.0]: 1.05
        # After rounding to epsilon-net: 1.1
        expected = 1.1
        
        assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"
        assert result >= 0, f"Result {result} is negative"
        
        results.append({
            "name": "lower_bound_clipping",
            "passed": True,
            "detail": f"Result {result} respects lower bound 0"
        })
    except Exception as e:
        results.append({
            "name": "lower_bound_clipping",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Upper bound clipping
    # Property: Large positive gradient step should be clipped to U
    try:
        lambda_t = 1.5
        eta = 1.0
        constraint_value = 2.0
        b_prime = 0.0
        U = 1.0
        epsilon = 0.1
        
        result = fn(lambda_t, eta, constraint_value, b_prime, U, epsilon)
        
        # Gradient step: 1.5 - 1.0 * (2.0 - 0.0) = 1.5 - 2.0 = -0.5
        # After clipping to [0, 1.0]: 0.0
        # After rounding to epsilon-net: 0.0
        expected = 0.0
        
        assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"
        assert result <= U, f"Result {result} exceeds upper bound {U}"
        
        results.append({
            "name": "upper_bound_clipping",
            "passed": True,
            "detail": f"Result {result} respects upper bound {U}"
        })
    except Exception as e:
        results.append({
            "name": "upper_bound_clipping",
            "passed": False,
            "detail": str(e)
        })
    
    return results
