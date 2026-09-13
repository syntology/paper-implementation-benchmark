import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero coefficients should yield zero gradient
    try:
        np.random.seed(42)
        D = 5
        k = 3
        grad_f = np.random.randn(D).astype(np.float64)
        grad_m = np.random.randn(k, D).astype(np.float64)
        c = np.zeros(k + 1, dtype=np.float64)
        
        result = fn(grad_f, grad_m, c)
        expected = np.zeros(D, dtype=np.float64)
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "Zero coefficients correctly yield zero gradient"
        results.append({"name": "zero_coefficients", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_coefficients", "passed": False, "detail": str(e)})
    
    # Test 2: Only fitness gradient (c[0]=1, others=0) should return grad_f
    try:
        np.random.seed(43)
        D = 7
        k = 4
        grad_f = np.random.randn(D).astype(np.float64)
        grad_m = np.random.randn(k, D).astype(np.float64)
        c = np.zeros(k + 1, dtype=np.float64)
        c[0] = 1.0
        
        result = fn(grad_f, grad_m, c)
        expected = grad_f.copy()
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "Fitness-only coefficient correctly returns grad_f"
        results.append({"name": "fitness_only", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "fitness_only", "passed": False, "detail": str(e)})
    
    # Test 3: Linearity - scaling all coefficients by alpha scales output by alpha
    try:
        np.random.seed(44)
        D = 6
        k = 2
        grad_f = np.random.randn(D).astype(np.float64)
        grad_m = np.random.randn(k, D).astype(np.float64)
        c = np.random.randn(k + 1).astype(np.float64)
        alpha = 2.5
        
        result1 = fn(grad_f, grad_m, c)
        result2 = fn(grad_f, grad_m, alpha * c)
        expected = alpha * result1
        
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result2 - expected))}" if not passed else "Coefficient scaling property holds"
        results.append({"name": "coefficient_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "coefficient_scaling", "passed": False, "detail": str(e)})
    
    # Test 4: Linearity - superposition principle
    try:
        np.random.seed(45)
        D = 8
        k = 3
        grad_f = np.random.randn(D).astype(np.float64)
        grad_m = np.random.randn(k, D).astype(np.float64)
        c1 = np.random.randn(k + 1).astype(np.float64)
        c2 = np.random.randn(k + 1).astype(np.float64)
        
        result1 = fn(grad_f, grad_m, c1)
        result2 = fn(grad_f, grad_m, c2)
        result_sum = fn(grad_f, grad_m, c1 + c2)
        expected = result1 + result2
        
        passed = np.allclose(result_sum, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result_sum - expected))}" if not passed else "Superposition principle holds"
        results.append({"name": "superposition", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "superposition", "passed": False, "detail": str(e)})
    
    # Test 5: Single measure gradient (k=1) with specific coefficients
    try:
        np.random.seed(46)
        D = 4
        k = 1
        grad_f = np.random.randn(D).astype(np.float64)
        grad_m = np.random.randn(k, D).astype(np.float64)
        c = np.array([0.3, 0.7], dtype=np.float64)
        
        result = fn(grad_f, grad_m, c)
        expected = 0.3 * grad_f + 0.7 * grad_m[0]
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "Manual computation matches for k=1"
        results.append({"name": "manual_k1", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "manual_k1", "passed": False, "detail": str(e)})
    
    return results
