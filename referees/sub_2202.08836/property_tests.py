import numpy as np

def check(fn):
    results = []
    
    # Test 1: Permutation invariance
    # The result should be the same regardless of the order of input scores
    try:
        np.random.seed(42)
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        alpha = 0.1
        result1 = fn(scores, alpha)
        
        permuted_scores = np.random.permutation(scores)
        result2 = fn(permuted_scores, alpha)
        
        passed = np.abs(result1 - result2) < 1e-6
        results.append({
            "name": "permutation_invariance",
            "passed": bool(passed),
            "detail": f"Original: {result1}, Permuted: {result2}, diff: {abs(result1 - result2)}"
        })
    except Exception as e:
        results.append({
            "name": "permutation_invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Monotonicity with respect to alpha
    # As alpha increases (less coverage), epsilon should decrease or stay the same
    try:
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        alpha1 = 0.05
        alpha2 = 0.2
        
        epsilon1 = fn(scores, alpha1)
        epsilon2 = fn(scores, alpha2)
        
        passed = epsilon1 >= epsilon2 - 1e-6
        results.append({
            "name": "monotonicity_alpha",
            "passed": bool(passed),
            "detail": f"epsilon(alpha=0.05)={epsilon1} >= epsilon(alpha=0.2)={epsilon2}"
        })
    except Exception as e:
        results.append({
            "name": "monotonicity_alpha",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Boundary case - alpha approaching 0
    # When alpha is very small, k = ceil((n+1)*(1-alpha)) - 1 approaches n
    # So epsilon should be the maximum value
    try:
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        alpha = 0.01  # Small alpha
        n = len(scores)
        # k = ceil((5+1)*(1-0.01)) - 1 = ceil(5.94) - 1 = 6 - 1 = 5 >= n=5
        epsilon = fn(scores, alpha)
        expected = np.max(scores)
        
        passed = np.abs(epsilon - expected) < 1e-6
        results.append({
            "name": "small_alpha_returns_max",
            "passed": bool(passed),
            "detail": f"epsilon={epsilon}, max={expected}, diff={abs(epsilon - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "small_alpha_returns_max",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Result is always within the range of input scores
    # epsilon should be in [min(scores), max(scores)]
    try:
        np.random.seed(123)
        scores = np.random.uniform(1.0, 10.0, 20)
        alpha = 0.1
        
        epsilon = fn(scores, alpha)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        passed = (epsilon >= min_score - 1e-6) and (epsilon <= max_score + 1e-6)
        results.append({
            "name": "result_within_bounds",
            "passed": bool(passed),
            "detail": f"min={min_score}, epsilon={epsilon}, max={max_score}"
        })
    except Exception as e:
        results.append({
            "name": "result_within_bounds",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Exact computation for known case
    # scores = [1, 2, 3, 4, 5], alpha = 0.2
    # k = ceil((5+1)*(1-0.2)) - 1 = ceil(4.8) - 1 = 5 - 1 = 4
    # sorted = [1, 2, 3, 4, 5], k=4 < n=5, so return sorted[4] = 5
    try:
        scores = np.array([3.0, 1.0, 5.0, 2.0, 4.0])
        alpha = 0.2
        epsilon = fn(scores, alpha)
        expected = 5.0
        
        passed = np.abs(epsilon - expected) < 1e-6
        results.append({
            "name": "exact_known_case",
            "passed": bool(passed),
            "detail": f"epsilon={epsilon}, expected={expected}, diff={abs(epsilon - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "exact_known_case",
            "passed": False,
            "detail": str(e)
        })
    
    return results
