import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output is always in [0, 1]
    try:
        test_cases = [
            (0.1, 0.5, 0.6),
            (1.0, -5.0, 5.0),
            (-2.0, 0.0, 0.0),
            (0.0, 100.0, -100.0),
            (10.0, -10.0, -5.0),
        ]
        all_in_range = True
        for epsilon, q_old, q_new in test_cases:
            m = fn(epsilon, q_old, q_new)
            if not (0.0 <= m <= 1.0):
                all_in_range = False
                break
        results.append({
            "name": "output_in_unit_interval",
            "passed": all_in_range,
            "detail": "All outputs should be in [0, 1]" if all_in_range else f"Output {m} outside [0, 1]"
        })
    except Exception as e:
        results.append({
            "name": "output_in_unit_interval",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: When q_new >> q_old, probability approaches 1
    try:
        epsilon = 0.5
        q_old = 0.0
        q_new = 100.0  # Large advantage for new plan
        m = fn(epsilon, q_old, q_new)
        threshold = 0.9999
        passed = m > threshold
        results.append({
            "name": "high_q_new_advantage_approaches_one",
            "passed": passed,
            "detail": f"When q_new >> q_old, m={m} should be > {threshold}"
        })
    except Exception as e:
        results.append({
            "name": "high_q_new_advantage_approaches_one",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: When q_new << q_old, probability approaches 0
    try:
        epsilon = 0.5
        q_old = 100.0
        q_new = 0.0  # Large disadvantage for new plan
        m = fn(epsilon, q_old, q_new)
        threshold = 0.0001
        passed = m < threshold
        results.append({
            "name": "low_q_new_advantage_approaches_zero",
            "passed": passed,
            "detail": f"When q_new << q_old, m={m} should be < {threshold}"
        })
    except Exception as e:
        results.append({
            "name": "low_q_new_advantage_approaches_zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: When q_new == q_old, probability depends only on epsilon
    # m = exp(q_new - q_old) / (exp(epsilon) + exp(q_new - q_old))
    #   = exp(0) / (exp(epsilon) + exp(0))
    #   = 1 / (exp(epsilon) + 1)
    try:
        epsilon = 0.5
        q_old = 5.0
        q_new = 5.0  # Equal Q-values
        m = fn(epsilon, q_old, q_new)
        expected = 1.0 / (np.exp(epsilon) + 1.0)
        passed = np.abs(m - expected) < 1e-6
        results.append({
            "name": "equal_q_values_closed_form",
            "passed": passed,
            "detail": f"When q_new == q_old, m={m} should equal 1/(exp(epsilon)+1)={expected}, diff={np.abs(m - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "equal_q_values_closed_form",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Monotonicity in q_new - q_old
    # As (q_new - q_old) increases, m should increase (monotonic)
    try:
        epsilon = 0.5
        q_old = 0.0
        deltas = [-5.0, -1.0, 0.0, 1.0, 5.0]
        probabilities = [fn(epsilon, q_old, q_old + delta) for delta in deltas]
        is_monotonic = all(probabilities[i] <= probabilities[i+1] for i in range(len(probabilities)-1))
        results.append({
            "name": "monotonicity_in_q_difference",
            "passed": is_monotonic,
            "detail": f"Probabilities {probabilities} should be monotonically increasing with q_new - q_old"
        })
    except Exception as e:
        results.append({
            "name": "monotonicity_in_q_difference",
            "passed": False,
            "detail": str(e)
        })
    
    return results
