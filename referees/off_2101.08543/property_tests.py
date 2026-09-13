import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape matches input shape
    try:
        N, D = 5, 3
        x_prime = np.random.randn(N, D).astype(np.float64)
        f_x = np.random.randn(N, D).astype(np.float64)
        output = fn(x_prime, f_x)
        
        passed = output.shape == (N, D)
        results.append({
            "name": "output_shape_matches_inputs",
            "passed": passed,
            "detail": f"Expected shape {(N, D)}, got {output.shape}"
        })
    except Exception as e:
        results.append({
            "name": "output_shape_matches_inputs",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Output dtype is float64
    try:
        N, D = 4, 2
        x_prime = np.random.randn(N, D).astype(np.float64)
        f_x = np.random.randn(N, D).astype(np.float64)
        output = fn(x_prime, f_x)
        
        passed = output.dtype == np.float64
        results.append({
            "name": "output_dtype_is_float64",
            "passed": passed,
            "detail": f"Expected dtype float64, got {output.dtype}"
        })
    except Exception as e:
        results.append({
            "name": "output_dtype_is_float64",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Element-wise subtraction property (Y_new = x_prime - f_x)
    try:
        np.random.seed(42)
        N, D = 6, 4
        x_prime = np.random.randn(N, D).astype(np.float64)
        f_x = np.random.randn(N, D).astype(np.float64)
        output = fn(x_prime, f_x)
        
        expected = x_prime - f_x
        passed = np.allclose(output, expected, atol=1e-6)
        results.append({
            "name": "element_wise_subtraction_correctness",
            "passed": passed,
            "detail": f"Max difference from expected: {np.max(np.abs(output - expected))}"
        })
    except Exception as e:
        results.append({
            "name": "element_wise_subtraction_correctness",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Zero residual when x_prime equals f_x
    try:
        np.random.seed(123)
        N, D = 3, 5
        x_prime = np.random.randn(N, D).astype(np.float64)
        f_x = x_prime.copy()
        output = fn(x_prime, f_x)
        
        expected_zeros = np.zeros((N, D), dtype=np.float64)
        passed = np.allclose(output, expected_zeros, atol=1e-6)
        results.append({
            "name": "zero_residual_when_equal",
            "passed": passed,
            "detail": f"Max absolute value in output: {np.max(np.abs(output))}"
        })
    except Exception as e:
        results.append({
            "name": "zero_residual_when_equal",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Linearity property (scaling inputs scales output)
    try:
        np.random.seed(456)
        N, D = 4, 3
        x_prime = np.random.randn(N, D).astype(np.float64)
        f_x = np.random.randn(N, D).astype(np.float64)
        
        scale = 2.5
        output1 = fn(x_prime, f_x)
        output2 = fn(scale * x_prime, scale * f_x)
        
        expected_scaled = scale * output1
        passed = np.allclose(output2, expected_scaled, atol=1e-6)
        results.append({
            "name": "linearity_under_scaling",
            "passed": passed,
            "detail": f"Max difference from scaled output: {np.max(np.abs(output2 - expected_scaled))}"
        })
    except Exception as e:
        results.append({
            "name": "linearity_under_scaling",
            "passed": False,
            "detail": str(e)
        })
    
    return results
