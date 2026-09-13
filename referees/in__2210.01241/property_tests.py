import numpy as np

def check(fn):
    results = []
    
    # Test 1: Permutation invariance - mean should be invariant to reordering
    try:
        np.random.seed(42)
        N = 10
        log_probs_new = np.random.randn(N) * 0.1
        log_probs_old = np.random.randn(N) * 0.1
        advantages = np.random.randn(N)
        epsilon = 0.2
        
        result1 = fn(log_probs_new, log_probs_old, advantages, epsilon)
        
        perm = np.random.permutation(N)
        result2 = fn(log_probs_new[perm], log_probs_old[perm], advantages[perm], epsilon)
        
        passed = np.abs(result1 - result2) < 1e-6
        results.append({
            "name": "Permutation invariance",
            "passed": bool(passed),
            "detail": f"Original: {result1}, Permuted: {result2}, diff: {np.abs(result1 - result2)}"
        })
    except Exception as e:
        results.append({
            "name": "Permutation invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: When log_probs are equal (ratio=1), objective should equal mean(advantages)
    try:
        np.random.seed(43)
        N = 10
        log_probs = np.random.randn(N) * 0.1
        advantages = np.random.randn(N)
        epsilon = 0.2
        
        result = fn(log_probs, log_probs, advantages, epsilon)
        expected = np.mean(advantages)
        
        passed = np.abs(result - expected) < 1e-6
        results.append({
            "name": "Identity case (ratio=1)",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected mean(advantages): {expected}, diff: {np.abs(result - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "Identity case (ratio=1)",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Advantage scaling - objective should scale linearly with advantages
    try:
        np.random.seed(44)
        N = 10
        log_probs_new = np.random.randn(N) * 0.1
        log_probs_old = np.random.randn(N) * 0.1
        advantages = np.random.randn(N)
        epsilon = 0.2
        scale = 2.5
        
        result1 = fn(log_probs_new, log_probs_old, advantages, epsilon)
        result2 = fn(log_probs_new, log_probs_old, advantages * scale, epsilon)
        
        passed = np.abs(result2 - result1 * scale) < 1e-6
        results.append({
            "name": "Advantage scaling linearity",
            "passed": bool(passed),
            "detail": f"Original: {result1}, Scaled: {result2}, Expected: {result1 * scale}, diff: {np.abs(result2 - result1 * scale)}"
        })
    except Exception as e:
        results.append({
            "name": "Advantage scaling linearity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Clipping bounds - when ratio is clipped, objective should be bounded
    try:
        np.random.seed(45)
        N = 5
        epsilon = 0.2
        advantages = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        
        # Case where ratio > 1 + epsilon (should clip to 1 + epsilon)
        log_probs_old = np.zeros(N)
        log_probs_new = np.ones(N) * 1.0  # ratio = exp(1) ≈ 2.718 > 1.2
        
        result = fn(log_probs_new, log_probs_old, advantages, epsilon)
        expected = (1 + epsilon) * np.mean(advantages)  # Should clip to 1 + epsilon
        
        passed = np.abs(result - expected) < 1e-6
        results.append({
            "name": "Clipping upper bound with positive advantages",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected (1+eps)*mean(adv): {expected}, diff: {np.abs(result - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "Clipping upper bound with positive advantages",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Zero advantages - objective should be zero
    try:
        np.random.seed(46)
        N = 10
        log_probs_new = np.random.randn(N) * 0.5
        log_probs_old = np.random.randn(N) * 0.5
        advantages = np.zeros(N)
        epsilon = 0.2
        
        result = fn(log_probs_new, log_probs_old, advantages, epsilon)
        
        passed = np.abs(result) < 1e-6
        results.append({
            "name": "Zero advantages",
            "passed": bool(passed),
            "detail": f"Result: {result}, Expected: 0.0, diff: {np.abs(result)}"
        })
    except Exception as e:
        results.append({
            "name": "Zero advantages",
            "passed": False,
            "detail": str(e)
        })
    
    return results
