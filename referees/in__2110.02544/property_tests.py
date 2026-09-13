import numpy as np

def check(fn):
    results = []
    
    # Test 1: Permutation invariance - mean should be invariant to reordering
    try:
        np.random.seed(42)
        N = 10
        log_probs_old = np.random.randn(N) * 0.5
        log_probs_new = np.random.randn(N) * 0.5
        advantages = np.random.randn(N) * 2.0
        epsilon = 0.2
        
        result1 = fn(log_probs_old, log_probs_new, advantages, epsilon)
        
        # Permute all arrays with same permutation
        perm = np.random.permutation(N)
        result2 = fn(log_probs_old[perm], log_probs_new[perm], advantages[perm], epsilon)
        
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
    
    # Test 2: When log_probs are equal (ratio=1), objective should equal mean(advantages) if no clipping occurs
    try:
        np.random.seed(43)
        N = 10
        log_probs = np.random.randn(N) * 0.5
        advantages = np.random.randn(N) * 2.0
        epsilon = 0.2
        
        result = fn(log_probs, log_probs, advantages, epsilon)
        expected = np.mean(advantages)
        
        passed = np.abs(result - expected) < 1e-6
        results.append({
            "name": "identity_policy_equals_mean_advantages",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected (mean advantages): {expected}, diff: {abs(result - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "identity_policy_equals_mean_advantages",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Scaling advantages by constant scales the objective by same constant
    try:
        np.random.seed(44)
        N = 10
        log_probs_old = np.random.randn(N) * 0.5
        log_probs_new = np.random.randn(N) * 0.5
        advantages = np.random.randn(N) * 2.0
        epsilon = 0.2
        scale = 3.0
        
        result1 = fn(log_probs_old, log_probs_new, advantages, epsilon)
        result2 = fn(log_probs_old, log_probs_new, advantages * scale, epsilon)
        
        expected_ratio = scale
        actual_ratio = result2 / result1 if result1 != 0 else (0.0 if result2 == 0 else np.inf)
        
        passed = np.abs(actual_ratio - expected_ratio) < 1e-6
        results.append({
            "name": "advantage_scaling_linearity",
            "passed": bool(passed),
            "detail": f"Result1: {result1}, Result2: {result2}, Expected ratio: {expected_ratio}, Actual ratio: {actual_ratio}"
        })
    except Exception as e:
        results.append({
            "name": "advantage_scaling_linearity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Clipping bounds - when ratio > 1+epsilon and advantages > 0, clipped version should be used
    try:
        N = 5
        epsilon = 0.2
        # Create scenario where ratio > 1+epsilon
        log_probs_old = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        log_probs_new = np.array([1.0, 1.0, 1.0, 1.0, 1.0])  # ratio = exp(1) ≈ 2.718 > 1.2
        advantages = np.array([1.0, 1.0, 1.0, 1.0, 1.0])  # all positive
        
        result = fn(log_probs_old, log_probs_new, advantages, epsilon)
        
        # Since ratio > 1+epsilon and advantages > 0, clipping should apply
        # min(ratio * adv, (1+epsilon) * adv) = (1+epsilon) * adv
        expected = (1 + epsilon) * np.mean(advantages)
        
        passed = np.abs(result - expected) < 1e-6
        results.append({
            "name": "upper_clipping_bound",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected: {expected}, diff: {abs(result - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "upper_clipping_bound",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Lower clipping bounds - when ratio < 1-epsilon and advantages > 0, clipped version should be used
    try:
        N = 5
        epsilon = 0.2
        # Create scenario where ratio < 1-epsilon
        log_probs_old = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        log_probs_new = np.array([-2.0, -2.0, -2.0, -2.0, -2.0])  # ratio = exp(-2) ≈ 0.135 < 0.8
        advantages = np.array([1.0, 1.0, 1.0, 1.0, 1.0])  # all positive
        
        result = fn(log_probs_old, log_probs_new, advantages, epsilon)
        
        # Since ratio < 1-epsilon and advantages > 0, clipping should apply
        # min(ratio * adv, (1-epsilon) * adv) = ratio * adv (since ratio < 1-epsilon)
        ratio = np.exp(-2.0)
        expected = ratio * np.mean(advantages)
        
        passed = np.abs(result - expected) < 1e-6
        results.append({
            "name": "lower_clipping_bound",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected: {expected}, diff: {abs(result - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "lower_clipping_bound",
            "passed": False,
            "detail": str(e)
        })
    
    return results
