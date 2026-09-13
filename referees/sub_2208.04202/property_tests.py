import numpy as np

def check(fn):
    results = []
    
    # Test 1: When t_now == t_next, output should equal input (no step taken)
    try:
        np.random.seed(42)
        x_t = np.random.randn(3, 4)
        x_pred = np.random.randn(3, 4)
        t = 0.5
        ns, ds, scale = 0.1, 0.2, 1.0
        
        x_next = fn(x_t, x_pred, t, t, ns, ds, scale)
        
        passed = np.allclose(x_next, x_t, atol=1e-6)
        detail = f"max diff: {np.max(np.abs(x_next - x_t))}" if not passed else "x_next == x_t when t_now == t_next"
        results.append({"name": "Identity when t_now == t_next", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Identity when t_now == t_next", "passed": False, "detail": str(e)})
    
    # Test 2: When x_pred is already clipped within bounds, clipping should not affect result
    try:
        np.random.seed(43)
        x_t = np.random.randn(2, 3) * 0.5
        x_pred = np.random.randn(2, 3) * 0.3  # Well within [-1, 1]
        t_now, t_next = 0.8, 0.6
        ns, ds, scale = 0.0, 0.0, 1.0
        
        x_next = fn(x_t, x_pred, t_now, t_next, ns, ds, scale)
        
        # Manually compute with pre-clipped x_pred (which should be unchanged)
        gamma_now = np.cos(((t_now + ns) / (1 + ds)) * np.pi / 2) ** 2
        gamma_next = np.cos(((t_next + ns) / (1 + ds)) * np.pi / 2) ** 2
        x_pred_clipped = np.clip(x_pred, -scale, scale)
        eps = (x_t - np.sqrt(gamma_now) * x_pred_clipped) / np.sqrt(1 - gamma_now)
        x_next_expected = np.sqrt(gamma_next) * x_pred_clipped + np.sqrt(1 - gamma_next) * eps
        
        passed = np.allclose(x_next, x_next_expected, atol=1e-6)
        detail = f"max diff: {np.max(np.abs(x_next - x_next_expected))}" if not passed else "Correct computation"
        results.append({"name": "Correct computation with unclipped x_pred", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Correct computation with unclipped x_pred", "passed": False, "detail": str(e)})
    
    # Test 3: Clipping bounds are respected - x_pred outside bounds should be clipped
    try:
        np.random.seed(44)
        x_t = np.array([[0.5, 0.5], [0.5, 0.5]])
        x_pred = np.array([[5.0, -5.0], [2.0, -2.0]])  # Outside [-1, 1]
        t_now, t_next = 0.7, 0.5
        ns, ds, scale = 0.0, 0.0, 1.0
        
        x_next = fn(x_t, x_pred, t_now, t_next, ns, ds, scale)
        
        # Compute with manually clipped x_pred
        gamma_now = np.cos(((t_now + ns) / (1 + ds)) * np.pi / 2) ** 2
        gamma_next = np.cos(((t_next + ns) / (1 + ds)) * np.pi / 2) ** 2
        x_pred_clipped = np.clip(x_pred, -scale, scale)  # Should be [[1, -1], [1, -1]]
        eps = (x_t - np.sqrt(gamma_now) * x_pred_clipped) / np.sqrt(1 - gamma_now)
        x_next_expected = np.sqrt(gamma_next) * x_pred_clipped + np.sqrt(1 - gamma_next) * eps
        
        passed = np.allclose(x_next, x_next_expected, atol=1e-6)
        detail = f"max diff: {np.max(np.abs(x_next - x_next_expected))}" if not passed else "Clipping correctly applied"
        results.append({"name": "Clipping bounds enforced", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Clipping bounds enforced", "passed": False, "detail": str(e)})
    
    # Test 4: At t=0, gamma should be 1, and at t=1, gamma should be 0 (with ns=0, ds=0)
    try:
        np.random.seed(45)
        x_t = np.random.randn(2, 2)
        x_pred = np.random.randn(2, 2) * 0.5
        ns, ds, scale = 0.0, 0.0, 1.0
        
        # At t_now=0, gamma_now = cos^2(0) = 1
        # At t_next close to 0, gamma_next also close to 1
        t_now, t_next = 0.0, 0.0
        x_next = fn(x_t, x_pred, t_now, t_next, ns, ds, scale)
        
        # When both gammas are 1, x_next should equal x_t (since eps term vanishes in limit)
        passed = np.allclose(x_next, x_t, atol=1e-6)
        detail = f"max diff: {np.max(np.abs(x_next - x_t))}" if not passed else "Correct at t=0"
        results.append({"name": "Degenerate case t=0", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Degenerate case t=0", "passed": False, "detail": str(e)})
    
    # Test 5: Shape preservation - output shape must match input shape
    try:
        np.random.seed(46)
        shapes = [(5,), (3, 4), (2, 3, 4)]
        all_passed = True
        
        for shape in shapes:
            x_t = np.random.randn(*shape)
            x_pred = np.random.randn(*shape) * 0.5
            t_now, t_next = 0.6, 0.4
            ns, ds, scale = 0.1, 0.1, 1.0
            
            x_next = fn(x_t, x_pred, t_now, t_next, ns, ds, scale)
            
            if x_next.shape != x_t.shape:
                all_passed = False
                break
        
        passed = all_passed
        detail = "All shapes preserved" if passed else f"Shape mismatch for shape {shape}"
        results.append({"name": "Shape preservation", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Shape preservation", "passed": False, "detail": str(e)})
    
    return results
