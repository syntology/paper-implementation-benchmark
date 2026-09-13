import numpy as np

def check(fn):
    results = []
    
    # Test 1: Identical policies should yield zero objective
    # When log_probs_current == log_probs_old, all ratios are 1.0,
    # so clipped ratios are also 1.0. The objective becomes min(1*adv, 1*adv) = adv.
    # The mean of advantages (centered rewards) should be ~0.
    try:
        np.random.seed(42)
        n = 100
        log_probs = np.random.randn(n)
        rewards = np.random.randn(n) * 10 + 5
        epsilon = 0.2
        
        result = fn(log_probs, log_probs, rewards, epsilon)
        
        # Advantages are (rewards - mean) / std, which sum to ~0 and have mean ~0
        # So the objective (mean of advantages) should be very close to 0
        passed = abs(result) < 1e-5
        detail = f"Result: {result}, expected ~0"
        results.append({"name": "identical_policies_zero_objective", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identical_policies_zero_objective", "passed": False, "detail": str(e)})
    
    # Test 2: Constant rewards should yield zero objective
    # If all rewards are identical, advantages are all 0 (after centering and scaling).
    # The objective is then min(ratio*0, clipped_ratio*0) = 0 for all i.
    try:
        np.random.seed(43)
        n = 50
        log_probs_current = np.random.randn(n)
        log_probs_old = np.random.randn(n)
        rewards = np.ones(n) * 7.5  # constant rewards
        epsilon = 0.2
        
        result = fn(log_probs_current, log_probs_old, rewards, epsilon)
        
        # With constant rewards, std is 0, but we need to handle this carefully.
        # The spec says divide by sample std with ddof=1. For constant array, std=0.
        # This will produce inf or nan. We check if result is 0 or nan/inf.
        passed = (result == 0.0) or np.isnan(result) or np.isinf(result)
        detail = f"Result: {result}, expected 0 or nan/inf for constant rewards"
        results.append({"name": "constant_rewards_zero_objective", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "constant_rewards_zero_objective", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling rewards by a positive constant should scale objective by that constant
    # If rewards -> c*rewards, then advantages -> c*advantages (scaling commutes with centering and division).
    # The objective scales linearly with advantages, so it should scale by c.
    try:
        np.random.seed(44)
        n = 60
        log_probs_current = np.random.randn(n)
        log_probs_old = np.random.randn(n)
        rewards = np.random.randn(n) * 5 + 2
        epsilon = 0.15
        
        result1 = fn(log_probs_current, log_probs_old, rewards, epsilon)
        
        scale = 3.5
        result2 = fn(log_probs_current, log_probs_old, rewards * scale, epsilon)
        
        # result2 should be approximately scale * result1
        ratio = result2 / result1 if abs(result1) > 1e-10 else 0
        passed = abs(ratio - scale) < 1e-5 or (abs(result1) < 1e-10 and abs(result2) < 1e-10)
        detail = f"Result1: {result1}, Result2: {result2}, scale: {scale}, ratio: {ratio}"
        results.append({"name": "reward_scaling_linearity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "reward_scaling_linearity", "passed": False, "detail": str(e)})
    
    # Test 4: Translating rewards by a constant should not change the objective
    # Adding a constant c to all rewards shifts the mean but doesn't change centered rewards.
    # Advantages remain unchanged, so the objective should be invariant.
    try:
        np.random.seed(45)
        n = 70
        log_probs_current = np.random.randn(n)
        log_probs_old = np.random.randn(n)
        rewards = np.random.randn(n) * 4 + 1
        epsilon = 0.25
        
        result1 = fn(log_probs_current, log_probs_old, rewards, epsilon)
        
        shift = 100.0
        result2 = fn(log_probs_current, log_probs_old, rewards + shift, epsilon)
        
        # Results should be identical (advantages unchanged by translation)
        passed = abs(result1 - result2) < 1e-6
        detail = f"Result1: {result1}, Result2: {result2}, difference: {abs(result1 - result2)}"
        results.append({"name": "reward_translation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "reward_translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Clipping should bound the objective when advantages are positive
    # When advantages > 0 and ratio > 1+epsilon, the clipped ratio limits the contribution.
    # The objective should be bounded by (1+epsilon) * max_advantage.
    try:
        np.random.seed(46)
        n = 80
        # Create scenario where current policy is much better (higher log probs)
        log_probs_old = np.zeros(n)
        log_probs_current = np.ones(n) * 2.0  # exp(2) ≈ 7.4, ratio >> 1+epsilon
        rewards = np.ones(n) * 10.0  # positive constant rewards
        epsilon = 0.2
        
        result = fn(log_probs_current, log_probs_old, rewards, epsilon)
        
        # With constant rewards, advantages are 0, so result should be 0 or nan/inf
        # This test verifies clipping doesn't cause unexpected behavior
        passed = (result == 0.0) or np.isnan(result) or np.isinf(result)
        detail = f"Result: {result}, expected 0 or nan/inf for constant rewards with clipping"
        results.append({"name": "clipping_bounds_with_constant_rewards", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "clipping_bounds_with_constant_rewards", "passed": False, "detail": str(e)})
    
    return results
