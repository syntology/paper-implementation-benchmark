import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output sums to 1 (normalization property)
    try:
        alpha_current = np.array([0.5, 0.3, 0.2])
        grad_losses = np.array([
            [1.0, 2.0, 3.0],
            [0.5, 1.5, 2.5],
            [2.0, 1.0, 0.5]
        ])
        eta_alpha = 0.1
        result = fn(alpha_current, grad_losses, eta_alpha)
        
        sum_result = np.sum(result)
        passed = np.isclose(sum_result, 1.0, atol=1e-6)
        detail = f"Sum of output: {sum_result}, expected 1.0"
        results.append({"name": "output_sums_to_one", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_sums_to_one", "passed": False, "detail": str(e)})
    
    # Test 2: Output is non-negative (weights must be non-negative)
    try:
        alpha_current = np.array([0.25, 0.25, 0.25, 0.25])
        grad_losses = np.array([
            [1.0, -1.0],
            [-2.0, 2.0],
            [0.5, -0.5],
            [-1.5, 1.5]
        ])
        eta_alpha = 0.5
        result = fn(alpha_current, grad_losses, eta_alpha)
        
        passed = np.all(result >= -1e-6)  # Allow tiny numerical errors
        detail = f"Min value: {np.min(result)}, all non-negative: {passed}"
        results.append({"name": "output_non_negative", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_non_negative", "passed": False, "detail": str(e)})
    
    # Test 3: Uniform input with zero gradients returns uniform output
    try:
        k = 5
        alpha_current = np.ones(k) / k
        grad_losses = np.zeros((k, 3))
        eta_alpha = 0.1
        result = fn(alpha_current, grad_losses, eta_alpha)
        
        expected = np.ones(k) / k
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"Result: {result}, expected: {expected}"
        results.append({"name": "uniform_zero_gradients", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "uniform_zero_gradients", "passed": False, "detail": str(e)})
    
    # Test 4: Output length matches input length
    try:
        alpha_current = np.array([0.1, 0.2, 0.3, 0.4])
        grad_losses = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
            [7.0, 8.0]
        ])
        eta_alpha = 0.05
        result = fn(alpha_current, grad_losses, eta_alpha)
        
        passed = len(result) == len(alpha_current) and result.ndim == 1
        detail = f"Output shape: {result.shape}, input length: {len(alpha_current)}"
        results.append({"name": "output_shape_matches_input", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_matches_input", "passed": False, "detail": str(e)})
    
    # Test 5: Small eta_alpha produces output close to uniform (limiting case)
    try:
        alpha_current = np.array([0.2, 0.3, 0.5])
        grad_losses = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])
        eta_alpha = 1e-8  # Very small step size
        result = fn(alpha_current, grad_losses, eta_alpha)
        
        # With tiny eta, exp(eta * inner_prod) ≈ 1, so output should be close to normalized input
        expected = alpha_current / np.sum(alpha_current)
        passed = np.allclose(result, expected, atol=1e-5)
        detail = f"Result: {result}, expected (normalized input): {expected}"
        results.append({"name": "small_eta_near_input", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "small_eta_near_input", "passed": False, "detail": str(e)})
    
    return results
