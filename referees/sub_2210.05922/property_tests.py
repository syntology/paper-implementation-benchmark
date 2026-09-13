import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape matches input shape
    try:
        q_real = np.array([1.0, 2.0, 3.0, 4.0])
        q_model = np.array([0.5, 1.5, 2.5, 3.5])
        alpha = 1.0
        output = fn(q_real, q_model, alpha)
        
        passed = output.shape == q_real.shape
        detail = f"Expected shape {q_real.shape}, got {output.shape}" if not passed else "Shape matches"
        results.append({"name": "output_shape_matches_input", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_matches_input", "passed": False, "detail": str(e)})
    
    # Test 2: All output weights are positive (exponential of any real number is positive)
    try:
        q_real = np.array([-5.0, 0.0, 5.0, 10.0])
        q_model = np.array([0.0, 0.0, 0.0, 0.0])
        alpha = 2.0
        output = fn(q_real, q_model, alpha)
        
        passed = np.all(output > 0)
        detail = f"Min weight: {np.min(output)}, all positive: {passed}" if passed else f"Found non-positive weights: {output[output <= 0]}"
        results.append({"name": "all_weights_positive", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "all_weights_positive", "passed": False, "detail": str(e)})
    
    # Test 3: When q_values_real == q_values_model, all weights equal exp(0) = 1.0
    try:
        q_values = np.array([1.5, 2.3, -0.7, 100.0])
        alpha = 3.5
        output = fn(q_values, q_values, alpha)
        
        expected = np.ones_like(q_values)
        passed = np.allclose(output, expected, atol=1e-6)
        detail = f"Expected all 1.0, got {output}" if not passed else "All weights equal 1.0"
        results.append({"name": "equal_qvalues_gives_unit_weights", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "equal_qvalues_gives_unit_weights", "passed": False, "detail": str(e)})
    
    # Test 4: Element-wise correctness: omega(s,a) = exp(alpha * (q_real - q_model))
    try:
        q_real = np.array([1.0, 2.0, 3.0])
        q_model = np.array([0.5, 1.0, 2.5])
        alpha = 0.5
        output = fn(q_real, q_model, alpha)
        
        expected = np.exp(alpha * (q_real - q_model))
        passed = np.allclose(output, expected, atol=1e-6)
        detail = f"Expected {expected}, got {output}" if not passed else "Element-wise formula correct"
        results.append({"name": "element_wise_formula_correctness", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "element_wise_formula_correctness", "passed": False, "detail": str(e)})
    
    # Test 5: Monotonicity: larger (q_real - q_model) produces larger weights
    try:
        q_real = np.array([5.0, 5.0, 5.0])
        q_model = np.array([1.0, 2.0, 3.0])  # differences: 4.0, 3.0, 2.0 (decreasing)
        alpha = 1.0
        output = fn(q_real, q_model, alpha)
        
        # output should be monotonically decreasing since differences are decreasing
        passed = np.all(np.diff(output) <= 1e-6)  # allowing for numerical error
        detail = f"Weights: {output}, monotonically decreasing: {passed}" if passed else f"Weights not monotonic: {output}"
        results.append({"name": "monotonicity_in_q_difference", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "monotonicity_in_q_difference", "passed": False, "detail": str(e)})
    
    return results
