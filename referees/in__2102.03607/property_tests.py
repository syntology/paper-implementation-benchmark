import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output is the exact difference of inputs
    # Property: epsilon = v_resampled - v_subset (by definition)
    try:
        v_resampled = 5.3
        v_subset = 2.1
        epsilon = fn(v_resampled, v_subset)
        expected = v_resampled - v_subset
        passed = np.isclose(epsilon, expected, atol=1e-6)
        results.append({
            "name": "output_is_exact_difference",
            "passed": passed,
            "detail": f"Expected {expected}, got {epsilon}" if not passed else "Pass"
        })
    except Exception as e:
        results.append({
            "name": "output_is_exact_difference",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Linearity in v_resampled
    # Property: compute_bootstrap_deviation(a + c, b) = compute_bootstrap_deviation(a, b) + c
    try:
        v_subset = 3.0
        v_resampled_1 = 7.5
        c = 2.3
        v_resampled_2 = v_resampled_1 + c
        
        epsilon_1 = fn(v_resampled_1, v_subset)
        epsilon_2 = fn(v_resampled_2, v_subset)
        
        expected_diff = c
        actual_diff = epsilon_2 - epsilon_1
        passed = np.isclose(actual_diff, expected_diff, atol=1e-6)
        results.append({
            "name": "linearity_in_v_resampled",
            "passed": passed,
            "detail": f"Expected difference {expected_diff}, got {actual_diff}" if not passed else "Pass"
        })
    except Exception as e:
        results.append({
            "name": "linearity_in_v_resampled",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Negative linearity in v_subset
    # Property: compute_bootstrap_deviation(a, b + c) = compute_bootstrap_deviation(a, b) - c
    try:
        v_resampled = 6.2
        v_subset_1 = 2.0
        c = 1.5
        v_subset_2 = v_subset_1 + c
        
        epsilon_1 = fn(v_resampled, v_subset_1)
        epsilon_2 = fn(v_resampled, v_subset_2)
        
        expected_diff = -c
        actual_diff = epsilon_2 - epsilon_1
        passed = np.isclose(actual_diff, expected_diff, atol=1e-6)
        results.append({
            "name": "negative_linearity_in_v_subset",
            "passed": passed,
            "detail": f"Expected difference {expected_diff}, got {actual_diff}" if not passed else "Pass"
        })
    except Exception as e:
        results.append({
            "name": "negative_linearity_in_v_subset",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Zero deviation when inputs are equal
    # Property: compute_bootstrap_deviation(v, v) = 0 (degenerate case)
    try:
        v = 4.7
        epsilon = fn(v, v)
        expected = 0.0
        passed = np.isclose(epsilon, expected, atol=1e-6)
        results.append({
            "name": "zero_deviation_when_equal",
            "passed": passed,
            "detail": f"Expected {expected}, got {epsilon}" if not passed else "Pass"
        })
    except Exception as e:
        results.append({
            "name": "zero_deviation_when_equal",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Sign consistency with input difference
    # Property: sign(epsilon) = sign(v_resampled - v_subset)
    try:
        test_cases = [
            (10.0, 3.0),   # positive epsilon
            (1.5, 8.2),    # negative epsilon
            (-5.0, -2.0),  # negative epsilon with negative values
            (-1.0, -3.0),  # positive epsilon with negative values
        ]
        all_passed = True
        for v_resampled, v_subset in test_cases:
            epsilon = fn(v_resampled, v_subset)
            expected_sign = np.sign(v_resampled - v_subset)
            actual_sign = np.sign(epsilon)
            if expected_sign != actual_sign:
                all_passed = False
                break
        
        results.append({
            "name": "sign_consistency",
            "passed": all_passed,
            "detail": "Pass" if all_passed else f"Sign mismatch for case ({v_resampled}, {v_subset})"
        })
    except Exception as e:
        results.append({
            "name": "sign_consistency",
            "passed": False,
            "detail": str(e)
        })
    
    return results
