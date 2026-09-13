import numpy as np

def check(fn):
    results = []
    
    # Test 1: Scaling property - gradient should scale linearly with lambda_scale
    try:
        np.random.seed(42)
        n = 3
        g_t = np.random.randint(0, 3, size=(n, n))
        y_hat = np.random.randn(4)
        y_target = np.random.randn(4)
        
        lambda1 = 1.0
        lambda2 = 2.5
        
        grad1 = fn(g_t, y_hat, y_target, lambda1)
        grad2 = fn(g_t, y_hat, y_target, lambda2)
        
        expected_grad2 = grad1 * (lambda2 / lambda1)
        passed = np.allclose(grad2, expected_grad2, atol=1e-6)
        detail = f"Scaling property: lambda2/lambda1={lambda2/lambda1}, max diff={np.max(np.abs(grad2 - expected_grad2))}"
        results.append({"name": "scaling_property", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_property", "passed": False, "detail": str(e)})
    
    # Test 2: Zero gradient when y_hat equals y_target (no guidance needed)
    try:
        np.random.seed(43)
        n = 3
        g_t = np.random.randint(0, 3, size=(n, n))
        y_hat = np.array([1.0, 2.0, 3.0])
        y_target = y_hat.copy()
        lambda_scale = 1.5
        
        grad = fn(g_t, y_hat, y_target, lambda_scale)
        
        passed = np.allclose(grad, 0.0, atol=1e-6)
        detail = f"Zero gradient when y_hat=y_target: max abs grad={np.max(np.abs(grad))}"
        results.append({"name": "zero_gradient_at_target", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_gradient_at_target", "passed": False, "detail": str(e)})
    
    # Test 3: Gradient is zero at positions where g_t[i,j] is at maximum (2)
    try:
        np.random.seed(44)
        n = 3
        g_t = np.full((n, n), 2)  # All entries at maximum
        y_hat = np.array([1.0, 2.0])
        y_target = np.array([3.0, 4.0])
        lambda_scale = 1.0
        
        grad = fn(g_t, y_hat, y_target, lambda_scale)
        
        passed = np.allclose(grad, 0.0, atol=1e-6)
        detail = f"Zero gradient at max values: max abs grad={np.max(np.abs(grad))}"
        results.append({"name": "zero_gradient_at_max", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_gradient_at_max", "passed": False, "detail": str(e)})
    
    # Test 4: Zero lambda_scale produces zero gradient
    try:
        np.random.seed(45)
        n = 3
        g_t = np.random.randint(0, 3, size=(n, n))
        y_hat = np.random.randn(3)
        y_target = np.random.randn(3)
        lambda_scale = 0.0
        
        grad = fn(g_t, y_hat, y_target, lambda_scale)
        
        passed = np.allclose(grad, 0.0, atol=1e-6)
        detail = f"Zero lambda produces zero gradient: max abs grad={np.max(np.abs(grad))}"
        results.append({"name": "zero_lambda_zero_gradient", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_lambda_zero_gradient", "passed": False, "detail": str(e)})
    
    # Test 5: Output shape matches input g_t shape
    try:
        np.random.seed(46)
        n = 4
        g_t = np.random.randint(0, 3, size=(n, n))
        y_hat = np.random.randn(5)
        y_target = np.random.randn(5)
        lambda_scale = 1.0
        
        grad = fn(g_t, y_hat, y_target, lambda_scale)
        
        passed = grad.shape == g_t.shape
        detail = f"Shape match: grad.shape={grad.shape}, g_t.shape={g_t.shape}"
        results.append({"name": "output_shape", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape", "passed": False, "detail": str(e)})
    
    return results
