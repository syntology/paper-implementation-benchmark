import numpy as np

def check(fn):
    results = []
    
    # Test 1: Limiting case tau=1 should return x_current exactly
    try:
        np.random.seed(42)
        N, D = 10, 5
        x_current = np.random.randn(N, D).astype(np.float64)
        x_residual = np.random.randn(N, D).astype(np.float64)
        tau = 1.0
        
        result = fn(x_current, x_residual, tau)
        expected = x_current
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "tau=1 returns x_current"
        results.append({"name": "limiting_case_tau_1", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "limiting_case_tau_1", "passed": False, "detail": str(e)})
    
    # Test 2: Limiting case tau=0 should return x_residual exactly
    try:
        np.random.seed(43)
        N, D = 10, 5
        x_current = np.random.randn(N, D).astype(np.float64)
        x_residual = np.random.randn(N, D).astype(np.float64)
        tau = 0.0
        
        result = fn(x_current, x_residual, tau)
        expected = x_residual
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "tau=0 returns x_residual"
        results.append({"name": "limiting_case_tau_0", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "limiting_case_tau_0", "passed": False, "detail": str(e)})
    
    # Test 3: Affine combination property - result should be convex combination when tau in [0,1]
    # Specifically: x_new - x_residual = tau * (x_current - x_residual)
    try:
        np.random.seed(44)
        N, D = 8, 4
        x_current = np.random.randn(N, D).astype(np.float64)
        x_residual = np.random.randn(N, D).astype(np.float64)
        tau = 0.3
        
        result = fn(x_current, x_residual, tau)
        # Verify the affine relationship
        lhs = result - x_residual
        rhs = tau * (x_current - x_residual)
        
        passed = np.allclose(lhs, rhs, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(lhs - rhs))}" if not passed else "affine combination verified"
        results.append({"name": "affine_combination_property", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "affine_combination_property", "passed": False, "detail": str(e)})
    
    # Test 4: Symmetry property - when x_current = x_residual, result should equal input regardless of tau
    try:
        np.random.seed(45)
        N, D = 6, 3
        x_same = np.random.randn(N, D).astype(np.float64)
        tau = 0.7
        
        result = fn(x_same, x_same, tau)
        expected = x_same
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "identical inputs return same output"
        results.append({"name": "identical_inputs_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identical_inputs_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Linearity in inputs - scaling both inputs by constant scales output by same constant
    try:
        np.random.seed(46)
        N, D = 7, 4
        x_current = np.random.randn(N, D).astype(np.float64)
        x_residual = np.random.randn(N, D).astype(np.float64)
        tau = 0.4
        scale = 2.5
        
        result1 = fn(x_current, x_residual, tau)
        result2 = fn(scale * x_current, scale * x_residual, tau)
        expected = scale * result1
        
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result2 - expected))}" if not passed else "scaling linearity verified"
        results.append({"name": "scaling_linearity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_linearity", "passed": False, "detail": str(e)})
    
    return results
