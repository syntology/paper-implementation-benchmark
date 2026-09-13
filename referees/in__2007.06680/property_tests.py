import numpy as np

def check(fn):
    results = []
    
    # Test 1: Degenerate case - beta_t = 1 should return g_current_theta_t
    # When beta_t = 1, the formula simplifies to u_t = 1 * g(tau_t | theta_t) + 0 * [...] = g(tau_t | theta_t)
    try:
        u_prev = np.array([1.0, 2.0, 3.0])
        g_current = np.array([0.5, 1.5, 2.5])
        g_prev = np.array([0.3, 1.2, 2.1])
        w_ratio = 0.95
        beta_t = 1.0
        
        result = fn(u_prev, g_current, g_prev, w_ratio, beta_t)
        expected = g_current
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"Expected {expected}, got {result}" if not passed else "Passed"
        results.append({"name": "beta_t=1 returns g_current_theta_t", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "beta_t=1 returns g_current_theta_t", "passed": False, "detail": str(e)})
    
    # Test 2: Degenerate case - beta_t = 0 should return u_{t-1} + g_current - w_ratio * g_prev
    # When beta_t = 0, u_t = 0 + 1 * [u_{t-1} + g(tau_t | theta_t) - w(tau_t | theta_{t-1}, theta_t) * g(tau_t | theta_{t-1})]
    try:
        u_prev = np.array([1.0, 2.0, 3.0])
        g_current = np.array([0.5, 1.5, 2.5])
        g_prev = np.array([0.3, 1.2, 2.1])
        w_ratio = 0.95
        beta_t = 0.0
        
        result = fn(u_prev, g_current, g_prev, w_ratio, beta_t)
        expected = u_prev + g_current - w_ratio * g_prev
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"Expected {expected}, got {result}" if not passed else "Passed"
        results.append({"name": "beta_t=0 returns u_prev + g_current - w_ratio*g_prev", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "beta_t=0 returns u_prev + g_current - w_ratio*g_prev", "passed": False, "detail": str(e)})
    
    # Test 3: Degenerate case - w_ratio = 1 and g_current = g_prev should simplify
    # When w_ratio = 1 and g_current = g_prev, the correction term vanishes:
    # u_t = beta_t * g + (1 - beta_t) * [u_{t-1} + g - 1 * g] = beta_t * g + (1 - beta_t) * u_{t-1}
    try:
        u_prev = np.array([1.0, 2.0, 3.0])
        g_current = np.array([0.5, 1.5, 2.5])
        g_prev = g_current.copy()
        w_ratio = 1.0
        beta_t = 0.7
        
        result = fn(u_prev, g_current, g_prev, w_ratio, beta_t)
        expected = beta_t * g_current + (1 - beta_t) * u_prev
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"Expected {expected}, got {result}" if not passed else "Passed"
        results.append({"name": "w_ratio=1 and g_current=g_prev simplifies to momentum blend", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "w_ratio=1 and g_current=g_prev simplifies to momentum blend", "passed": False, "detail": str(e)})
    
    # Test 4: Output shape and type preservation
    # The output should be a 1-D numpy array with the same shape as input vectors
    try:
        u_prev = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        g_current = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        g_prev = np.array([0.05, 0.15, 0.25, 0.35, 0.45])
        w_ratio = 0.9
        beta_t = 0.5
        
        result = fn(u_prev, g_current, g_prev, w_ratio, beta_t)
        
        passed = (isinstance(result, np.ndarray) and 
                 result.ndim == 1 and 
                 result.shape == u_prev.shape and
                 result.dtype in [np.float32, np.float64])
        detail = f"Shape: {result.shape}, dtype: {result.dtype}, ndim: {result.ndim}" if passed else f"Invalid output: shape={result.shape if hasattr(result, 'shape') else 'N/A'}, dtype={result.dtype if hasattr(result, 'dtype') else 'N/A'}"
        results.append({"name": "Output is 1-D numpy array with correct shape", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Output is 1-D numpy array with correct shape", "passed": False, "detail": str(e)})
    
    # Test 5: Linearity in u_prev when beta_t = 0
    # When beta_t = 0, u_t is linear in u_prev: u_t = u_prev + g_current - w_ratio * g_prev
    # So u_t(c * u_prev) = c * u_t(u_prev) for any scalar c
    try:
        u_prev = np.array([1.0, 2.0, 3.0])
        g_current = np.array([0.5, 1.5, 2.5])
        g_prev = np.array([0.3, 1.2, 2.1])
        w_ratio = 0.95
        beta_t = 0.0
        c = 2.5
        
        result1 = fn(u_prev, g_current, g_prev, w_ratio, beta_t)
        result2 = fn(c * u_prev, g_current, g_prev, w_ratio, beta_t)
        expected = c * result1
        
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = f"Expected {expected}, got {result2}" if not passed else "Passed"
        results.append({"name": "Linearity in u_prev when beta_t=0", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Linearity in u_prev when beta_t=0", "passed": False, "detail": str(e)})
    
    return results
