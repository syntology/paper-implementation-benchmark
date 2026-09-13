import numpy as np

def check(fn):
    results = []
    
    # Test 1: At t_prime = 1, theta should equal theta_base (z(1) = 0, exp(0) = 1)
    try:
        d_model = 128
        theta = fn(t_prime=1.0, t_train=100.0, d_model=d_model, lambda_factor=0.5)
        
        # Compute expected theta_base
        i = np.arange(d_model // 2)
        theta_base = 10000.0 ** (-2 * i / d_model)
        
        # At t_prime=1, z(1)=0, so theta_{t_prime} = theta_base * exp(0) = theta_base
        passed = np.allclose(theta, theta_base, rtol=1e-6, atol=1e-9)
        detail = f"Max diff: {np.max(np.abs(theta - theta_base))}" if not passed else "Passed"
        results.append({"name": "boundary_condition_t_prime_equals_1", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "boundary_condition_t_prime_equals_1", "passed": False, "detail": str(e)})
    
    # Test 2: Monotonicity with respect to t_prime (for lambda_factor > 0)
    # As t_prime increases, z(t_prime) = log(1 + (t_prime - 1) * lambda) increases,
    # so theta should increase element-wise
    try:
        d_model = 64
        t_train = 100.0
        lambda_factor = 0.5
        
        t1 = 10.0
        t2 = 50.0
        theta_t1 = fn(t_prime=t1, t_train=t_train, d_model=d_model, lambda_factor=lambda_factor)
        theta_t2 = fn(t_prime=t2, t_train=t_train, d_model=d_model, lambda_factor=lambda_factor)
        
        # All elements should be strictly larger at t2 than t1
        passed = np.all(theta_t2 > theta_t1)
        detail = f"Min ratio t2/t1: {np.min(theta_t2 / theta_t1)}" if not passed else "Passed"
        results.append({"name": "monotonicity_increasing_with_t_prime", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "monotonicity_increasing_with_t_prime", "passed": False, "detail": str(e)})
    
    # Test 3: Positivity - theta values must always be positive
    try:
        d_model = 256
        t_train = 1000.0
        lambda_factor = 2.0
        
        # Test at multiple time points
        t_primes = np.array([1.0, 10.0, 100.0, 500.0, 1000.0])
        all_positive = True
        min_val = float('inf')
        
        for t_prime in t_primes:
            theta = fn(t_prime=t_prime, t_train=t_train, d_model=d_model, lambda_factor=lambda_factor)
            all_positive = all_positive and np.all(theta > 0)
            min_val = min(min_val, np.min(theta))
        
        passed = all_positive
        detail = f"Min value across all tests: {min_val}" if not passed else "Passed"
        results.append({"name": "positivity_of_theta", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "positivity_of_theta", "passed": False, "detail": str(e)})
    
    # Test 4: Output shape and dtype correctness
    try:
        d_model = 512
        theta = fn(t_prime=50.0, t_train=100.0, d_model=d_model, lambda_factor=1.0)
        
        expected_shape = (d_model // 2,)
        shape_correct = theta.shape == expected_shape
        dtype_correct = theta.dtype == np.float64
        
        passed = shape_correct and dtype_correct
        detail = f"Shape: {theta.shape} (expected {expected_shape}), dtype: {theta.dtype} (expected float64)"
        results.append({"name": "output_shape_and_dtype", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_and_dtype", "passed": False, "detail": str(e)})
    
    # Test 5: ODE solution verification - z(t) = log(1 + (t-1)*lambda)
    # Therefore theta(t) = theta_base * exp(log(1 + (t-1)*lambda)) = theta_base * (1 + (t-1)*lambda)
    try:
        d_model = 128
        t_prime = 25.0
        t_train = 100.0
        lambda_factor = 0.3
        
        theta = fn(t_prime=t_prime, t_train=t_train, d_model=d_model, lambda_factor=lambda_factor)
        
        # Compute expected value
        i = np.arange(d_model // 2)
        theta_base = 10000.0 ** (-2 * i / d_model)
        z_t_prime = np.log(1.0 + (t_prime - 1.0) * lambda_factor)
        expected_theta = theta_base * np.exp(z_t_prime)
        
        passed = np.allclose(theta, expected_theta, rtol=1e-6, atol=1e-9)
        detail = f"Max relative error: {np.max(np.abs((theta - expected_theta) / expected_theta))}" if not passed else "Passed"
        results.append({"name": "ode_solution_correctness", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "ode_solution_correctness", "passed": False, "detail": str(e)})
    
    return results
