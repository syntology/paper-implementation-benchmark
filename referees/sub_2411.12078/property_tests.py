import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity
    # Property: All scores must be non-negative since counts and properties are non-negative
    try:
        fragment_counts = np.array([0, 5, 10, 3])
        fragment_properties = np.array([
            [1.0, 2.0, 3.0],
            [0.5, 1.5, 2.5],
            [0.0, 0.0, 0.0],
            [2.0, 2.0, 2.0]
        ])
        scores = fn(fragment_counts, fragment_properties)
        passed = np.all(scores >= 0)
        detail = f"All scores non-negative: {passed}. Scores: {scores}"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Zero count yields zero score
    # Property: If fragment_counts[i] = 0, then score[i] = 0 regardless of properties
    try:
        fragment_counts = np.array([0, 5, 0])
        fragment_properties = np.array([
            [10.0, 20.0, 30.0],
            [1.0, 2.0, 3.0],
            [100.0, 200.0, 300.0]
        ])
        scores = fn(fragment_counts, fragment_properties)
        passed = (scores[0] == 0.0) and (scores[2] == 0.0)
        detail = f"Zero counts produce zero scores: {passed}. Scores: {scores}"
        results.append({"name": "zero_count_zero_score", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_count_zero_score", "passed": False, "detail": str(e)})
    
    # Test 3: Zero properties (P=0) treated as mean=1.0
    # Property: score[i] = fragment_counts[i] * 1.0 when P=0
    try:
        fragment_counts = np.array([3, 7, 2])
        fragment_properties = np.empty((3, 0))  # P=0
        scores = fn(fragment_counts, fragment_properties)
        expected = fragment_counts * 1.0
        passed = np.allclose(scores, expected, atol=1e-6)
        detail = f"P=0 case: expected {expected}, got {scores}. Match: {passed}"
        results.append({"name": "zero_properties_mean_one", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_properties_mean_one", "passed": False, "detail": str(e)})
    
    # Test 4: Correctness of mean computation
    # Property: score[i] = fragment_counts[i] * mean(fragment_properties[i, :])
    # Verify with known values
    try:
        fragment_counts = np.array([2, 4, 1])
        fragment_properties = np.array([
            [1.0, 3.0, 5.0],      # mean = 3.0, score = 2 * 3.0 = 6.0
            [2.0, 2.0, 2.0],      # mean = 2.0, score = 4 * 2.0 = 8.0
            [10.0],                # mean = 10.0, score = 1 * 10.0 = 10.0
        ])
        scores = fn(fragment_counts, fragment_properties)
        expected = np.array([6.0, 8.0, 10.0])
        passed = np.allclose(scores, expected, atol=1e-6)
        detail = f"Mean computation: expected {expected}, got {scores}. Match: {passed}"
        results.append({"name": "mean_computation", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "mean_computation", "passed": False, "detail": str(e)})
    
    # Test 5: Scaling invariance of properties
    # Property: If all properties for fragment i are scaled by constant k,
    # then score[i] scales by k (since mean scales by k)
    try:
        fragment_counts = np.array([5, 3])
        fragment_properties_base = np.array([
            [1.0, 2.0, 3.0],
            [2.0, 4.0, 6.0]
        ])
        scores_base = fn(fragment_counts, fragment_properties_base)
        
        k = 2.5
        fragment_properties_scaled = fragment_properties_base * k
        scores_scaled = fn(fragment_counts, fragment_properties_scaled)
        
        expected_scaled = scores_base * k
        passed = np.allclose(scores_scaled, expected_scaled, atol=1e-6)
        detail = f"Scaling k={k}: expected {expected_scaled}, got {scores_scaled}. Match: {passed}"
        results.append({"name": "property_scaling_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "property_scaling_invariance", "passed": False, "detail": str(e)})
    
    return results
