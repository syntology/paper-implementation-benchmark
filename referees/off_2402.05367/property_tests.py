import numpy as np

def check(fn):
    results = []
    
    # Test 1: Gain is difference of first two columns
    # Property: The returned value must equal f_samples[:, 0] - f_samples[:, 1] for at least one row
    try:
        np.random.seed(42)
        n_samples = 5
        f_samples = np.random.randn(n_samples, 10)
        x = np.array([1.0, 2.0])
        x_ref = np.array([3.0, 4.0])
        
        result = fn(x, x_ref, f_samples)
        expected_gains = f_samples[:, 0] - f_samples[:, 1]
        expected_max = np.max(expected_gains)
        
        passed = np.isclose(result, expected_max, atol=1e-6)
        results.append({
            "name": "gain_is_max_of_differences",
            "passed": passed,
            "detail": f"Expected {expected_max}, got {result}" if not passed else "Correct"
        })
    except Exception as e:
        results.append({
            "name": "gain_is_max_of_differences",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Single sample returns that sample's gain
    # Property: With 1 sample, output equals f_samples[0, 0] - f_samples[0, 1]
    try:
        np.random.seed(43)
        f_samples = np.array([[5.0, 2.0, 999.0]])  # extra columns ignored
        x = np.array([1.0])
        x_ref = np.array([2.0])
        
        result = fn(x, x_ref, f_samples)
        expected = 5.0 - 2.0
        
        passed = np.isclose(result, expected, atol=1e-6)
        results.append({
            "name": "single_sample_returns_gain",
            "passed": passed,
            "detail": f"Expected {expected}, got {result}" if not passed else "Correct"
        })
    except Exception as e:
        results.append({
            "name": "single_sample_returns_gain",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Result is maximum, not minimum or mean
    # Property: Result >= all individual gains (it's the max)
    try:
        np.random.seed(44)
        f_samples = np.array([
            [1.0, 0.5],
            [2.0, 1.0],
            [0.5, 0.8],
            [3.0, 1.5]
        ])
        x = np.array([1.0])
        x_ref = np.array([2.0])
        
        result = fn(x, x_ref, f_samples)
        gains = f_samples[:, 0] - f_samples[:, 1]
        
        # Result should equal max gain and be >= all gains
        passed = np.isclose(result, np.max(gains), atol=1e-6) and np.all(result >= gains - 1e-6)
        results.append({
            "name": "result_is_maximum_gain",
            "passed": passed,
            "detail": f"Result {result}, max gain {np.max(gains)}, all gains {gains}" if not passed else "Correct"
        })
    except Exception as e:
        results.append({
            "name": "result_is_maximum_gain",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Invariance to x and x_ref values (only columns 0 and 1 matter)
    # Property: Result depends only on f_samples[:, 0] and f_samples[:, 1], not on x, x_ref, or extra columns
    try:
        np.random.seed(45)
        f_samples = np.array([
            [1.0, 0.5, 999.0, -999.0],
            [2.0, 1.0, 888.0, -888.0],
            [0.5, 0.8, 777.0, -777.0]
        ])
        
        # Call with different x, x_ref values
        result1 = fn(np.array([1.0, 2.0]), np.array([3.0, 4.0]), f_samples)
        result2 = fn(np.array([10.0, 20.0]), np.array([30.0, 40.0]), f_samples)
        result3 = fn(np.array([-1.0, -2.0]), np.array([-3.0, -4.0]), f_samples)
        
        # All should be identical since f_samples is the same
        passed = np.isclose(result1, result2, atol=1e-6) and np.isclose(result2, result3, atol=1e-6)
        results.append({
            "name": "invariant_to_x_xref_values",
            "passed": passed,
            "detail": f"Results: {result1}, {result2}, {result3}" if not passed else "Correct"
        })
    except Exception as e:
        results.append({
            "name": "invariant_to_x_xref_values",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Scaling property - if all f_samples are scaled by constant c, result scales by c
    # Property: fn(..., c * f_samples) = c * fn(..., f_samples) for c > 0
    try:
        np.random.seed(46)
        f_samples = np.array([
            [1.0, 0.5],
            [2.0, 1.0],
            [0.5, 0.8]
        ])
        x = np.array([1.0, 2.0])
        x_ref = np.array([3.0, 4.0])
        
        result_original = fn(x, x_ref, f_samples)
        
        c = 2.5
        result_scaled = fn(x, x_ref, c * f_samples)
        expected_scaled = c * result_original
        
        passed = np.isclose(result_scaled, expected_scaled, atol=1e-6)
        results.append({
            "name": "scaling_invariance",
            "passed": passed,
            "detail": f"Expected {expected_scaled}, got {result_scaled}" if not passed else "Correct"
        })
    except Exception as e:
        results.append({
            "name": "scaling_invariance",
            "passed": False,
            "detail": str(e)
        })
    
    return results
