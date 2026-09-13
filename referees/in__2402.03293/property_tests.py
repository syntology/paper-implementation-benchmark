import numpy as np

def check(fn):
    results = []
    np.random.seed(42)
    
    # Test 1: Beta = 0 should ignore momentum and return only gradient term
    try:
        n, r, m = 5, 3, 4
        M_t = np.random.randn(n, r)
        G_t = np.random.randn(n, m)
        A_current = np.random.randn(r, m)
        A_next = np.random.randn(r, m)
        beta = 0.0
        
        # Test both reseed and non-reseed cases
        result_reseed = fn(M_t, G_t, A_current, A_next, beta, True)
        result_no_reseed = fn(M_t, G_t, A_current, A_next, beta, False)
        expected = G_t @ A_next.T
        
        passed_reseed = np.allclose(result_reseed, expected, atol=1e-6)
        passed_no_reseed = np.allclose(result_no_reseed, expected, atol=1e-6)
        passed = passed_reseed and passed_no_reseed
        
        results.append({
            "name": "Beta=0 returns only gradient term",
            "passed": passed,
            "detail": f"Reseed: {passed_reseed}, No-reseed: {passed_no_reseed}"
        })
    except Exception as e:
        results.append({
            "name": "Beta=0 returns only gradient term",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Beta = 1 with zero gradient should return only momentum term
    try:
        n, r, m = 5, 3, 4
        M_t = np.random.randn(n, r)
        G_t = np.zeros((n, m))
        A_current = np.random.randn(r, m)
        A_next = np.random.randn(r, m)
        beta = 1.0
        
        # Non-reseed: M_next = M_t
        result_no_reseed = fn(M_t, G_t, A_current, A_next, beta, False)
        passed_no_reseed = np.allclose(result_no_reseed, M_t, atol=1e-6)
        
        # Reseed: M_next = M_t @ A_current @ A_next.T
        result_reseed = fn(M_t, G_t, A_current, A_next, beta, True)
        expected_reseed = M_t @ A_current @ A_next.T
        passed_reseed = np.allclose(result_reseed, expected_reseed, atol=1e-6)
        
        passed = passed_reseed and passed_no_reseed
        
        results.append({
            "name": "Beta=1 with zero gradient returns momentum only",
            "passed": passed,
            "detail": f"Reseed: {passed_reseed}, No-reseed: {passed_no_reseed}"
        })
    except Exception as e:
        results.append({
            "name": "Beta=1 with zero gradient returns momentum only",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Output shape is always n×r
    try:
        n, r, m = 6, 4, 5
        M_t = np.random.randn(n, r)
        G_t = np.random.randn(n, m)
        A_current = np.random.randn(r, m)
        A_next = np.random.randn(r, m)
        beta = 0.5
        
        result_reseed = fn(M_t, G_t, A_current, A_next, beta, True)
        result_no_reseed = fn(M_t, G_t, A_current, A_next, beta, False)
        
        passed = (result_reseed.shape == (n, r) and result_no_reseed.shape == (n, r))
        
        results.append({
            "name": "Output shape is n×r",
            "passed": passed,
            "detail": f"Reseed shape: {result_reseed.shape}, No-reseed shape: {result_no_reseed.shape}, Expected: ({n}, {r})"
        })
    except Exception as e:
        results.append({
            "name": "Output shape is n×r",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Linear combination property - result is linear in G_t when beta < 1
    try:
        n, r, m = 4, 3, 3
        M_t = np.random.randn(n, r)
        G_t1 = np.random.randn(n, m)
        G_t2 = np.random.randn(n, m)
        A_current = np.random.randn(r, m)
        A_next = np.random.randn(r, m)
        beta = 0.7
        alpha = 2.5
        
        # For non-reseed case: M_next = beta * M_t + (1-beta) * G_t @ A_next.T
        # Should satisfy: f(alpha*G) = beta*M_t + (1-beta)*alpha*G@A_next.T
        result1 = fn(M_t, G_t1, A_current, A_next, beta, False)
        result2 = fn(M_t, alpha * G_t1, A_current, A_next, beta, False)
        
        # result2 should equal beta*M_t + alpha*(1-beta)*G_t1@A_next.T
        # result1 = beta*M_t + (1-beta)*G_t1@A_next.T
        # So: result2 - beta*M_t = alpha*(result1 - beta*M_t)
        diff1 = result1 - beta * M_t
        diff2 = result2 - beta * M_t
        
        passed = np.allclose(diff2, alpha * diff1, atol=1e-6)
        
        results.append({
            "name": "Linear scaling in gradient G_t",
            "passed": passed,
            "detail": f"Scaling property holds: {passed}"
        })
    except Exception as e:
        results.append({
            "name": "Linear scaling in gradient G_t",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Zero momentum and zero gradient yields zero output
    try:
        n, r, m = 4, 3, 5
        M_t = np.zeros((n, r))
        G_t = np.zeros((n, m))
        A_current = np.random.randn(r, m)
        A_next = np.random.randn(r, m)
        beta = 0.6
        
        result_reseed = fn(M_t, G_t, A_current, A_next, beta, True)
        result_no_reseed = fn(M_t, G_t, A_current, A_next, beta, False)
        
        passed = (np.allclose(result_reseed, 0, atol=1e-6) and 
                  np.allclose(result_no_reseed, 0, atol=1e-6))
        
        results.append({
            "name": "Zero inputs yield zero output",
            "passed": passed,
            "detail": f"Both cases return zero: {passed}"
        })
    except Exception as e:
        results.append({
            "name": "Zero inputs yield zero output",
            "passed": False,
            "detail": str(e)
        })
    
    return results
