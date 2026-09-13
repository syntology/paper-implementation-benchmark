import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output dimension matches input dimension
    try:
        d = 5
        full_grad = np.random.RandomState(42).randn(d)
        local_grad = np.random.RandomState(43).randn(d)
        result = fn(full_grad, local_grad)
        passed = isinstance(result, np.ndarray) and result.shape == (d,)
        results.append({
            "name": "output_dimension_matches_input",
            "passed": passed,
            "detail": f"Expected shape ({d},), got {result.shape if isinstance(result, np.ndarray) else type(result)}"
        })
    except Exception as e:
        results.append({
            "name": "output_dimension_matches_input",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Correctness of subtraction (g_k = full_grad - local_grad)
    try:
        np.random.seed(44)
        d = 7
        full_grad = np.random.randn(d)
        local_grad = np.random.randn(d)
        expected = full_grad - local_grad
        result = fn(full_grad, local_grad)
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "correctness_subtraction",
            "passed": passed,
            "detail": f"Max difference: {np.max(np.abs(result - expected)) if isinstance(result, np.ndarray) else 'N/A'}"
        })
    except Exception as e:
        results.append({
            "name": "correctness_subtraction",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Zero correction when full_grad equals local_grad
    try:
        np.random.seed(45)
        d = 6
        grad = np.random.randn(d)
        result = fn(grad, grad)
        expected = np.zeros(d)
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "zero_correction_identical_gradients",
            "passed": passed,
            "detail": f"Max absolute value in result: {np.max(np.abs(result)) if isinstance(result, np.ndarray) else 'N/A'}"
        })
    except Exception as e:
        results.append({
            "name": "zero_correction_identical_gradients",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Linearity in full_grad (scaling full_grad scales output)
    try:
        np.random.seed(46)
        d = 4
        full_grad = np.random.randn(d)
        local_grad = np.random.randn(d)
        scale = 2.5
        
        result1 = fn(full_grad, local_grad)
        result2 = fn(scale * full_grad, local_grad)
        expected_scaled = scale * result1
        
        passed = np.allclose(result2, expected_scaled, atol=1e-6)
        results.append({
            "name": "linearity_in_full_grad",
            "passed": passed,
            "detail": f"Max difference: {np.max(np.abs(result2 - expected_scaled)) if isinstance(result2, np.ndarray) else 'N/A'}"
        })
    except Exception as e:
        results.append({
            "name": "linearity_in_full_grad",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Negation property (swapping inputs negates output)
    try:
        np.random.seed(47)
        d = 5
        full_grad = np.random.randn(d)
        local_grad = np.random.randn(d)
        
        result1 = fn(full_grad, local_grad)
        result2 = fn(local_grad, full_grad)
        expected_negated = -result1
        
        passed = np.allclose(result2, expected_negated, atol=1e-6)
        results.append({
            "name": "negation_on_swap",
            "passed": passed,
            "detail": f"Max difference: {np.max(np.abs(result2 - expected_negated)) if isinstance(result2, np.ndarray) else 'N/A'}"
        })
    except Exception as e:
        results.append({
            "name": "negation_on_swap",
            "passed": False,
            "detail": str(e)
        })
    
    return results
