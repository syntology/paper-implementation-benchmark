import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity
    # The loss is MSE, which is always >= 0
    try:
        np.random.seed(42)
        N, D = 5, 3
        v_theta = np.random.randn(N, D)
        t = 0.5
        x_t = np.random.randn(N, D)
        u_t = np.random.randn(N, D)
        
        loss = fn(v_theta, t, x_t, u_t)
        
        passed = loss >= 0.0
        detail = f"Loss value: {loss}" if passed else f"Loss is negative: {loss}"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Zero loss when predictions match targets
    # When v_theta == u_t, loss should be exactly 0
    try:
        np.random.seed(43)
        N, D = 4, 2
        u_t = np.random.randn(N, D)
        v_theta = u_t.copy()
        t = 0.3
        x_t = np.random.randn(N, D)
        
        loss = fn(v_theta, t, x_t, u_t)
        
        passed = np.abs(loss) < 1e-6
        detail = f"Loss when v_theta == u_t: {loss}" if passed else f"Expected ~0, got {loss}"
        results.append({"name": "zero_loss_perfect_match", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_loss_perfect_match", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling invariance of difference
    # If both v_theta and u_t are scaled by the same factor k, loss scales by k^2
    try:
        np.random.seed(44)
        N, D = 3, 4
        v_theta = np.random.randn(N, D)
        u_t = np.random.randn(N, D)
        t = 0.7
        x_t = np.random.randn(N, D)
        
        loss1 = fn(v_theta, t, x_t, u_t)
        
        k = 2.5
        loss2 = fn(k * v_theta, t, x_t, k * u_t)
        
        expected_loss2 = k**2 * loss1
        passed = np.abs(loss2 - expected_loss2) < 1e-5 * (np.abs(expected_loss2) + 1e-8)
        detail = f"Loss1: {loss1}, Loss2: {loss2}, Expected: {expected_loss2}" if passed else f"Scaling failed: got {loss2}, expected {expected_loss2}"
        results.append({"name": "scaling_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 4: Time parameter does not affect loss
    # The loss should be identical for different values of t (per spec)
    try:
        np.random.seed(45)
        N, D = 6, 2
        v_theta = np.random.randn(N, D)
        u_t = np.random.randn(N, D)
        x_t = np.random.randn(N, D)
        
        loss_t1 = fn(v_theta, 0.2, x_t, u_t)
        loss_t2 = fn(v_theta, 0.8, x_t, u_t)
        loss_t3 = fn(v_theta, 0.5, x_t, u_t)
        
        passed = (np.abs(loss_t1 - loss_t2) < 1e-6 and 
                  np.abs(loss_t2 - loss_t3) < 1e-6)
        detail = f"Losses at t=0.2, 0.8, 0.5: {loss_t1}, {loss_t2}, {loss_t3}" if passed else "Time parameter affected loss"
        results.append({"name": "time_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "time_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Batch averaging property
    # Loss should be the mean of element-wise squared differences
    try:
        np.random.seed(46)
        N, D = 3, 2
        v_theta = np.random.randn(N, D)
        u_t = np.random.randn(N, D)
        t = 0.5
        x_t = np.random.randn(N, D)
        
        loss = fn(v_theta, t, x_t, u_t)
        
        # Manually compute expected loss
        diff = v_theta - u_t
        expected_loss = np.mean(diff ** 2)
        
        passed = np.abs(loss - expected_loss) < 1e-6
        detail = f"Computed loss: {loss}, Expected: {expected_loss}" if passed else f"Mismatch: {loss} vs {expected_loss}"
        results.append({"name": "batch_averaging", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "batch_averaging", "passed": False, "detail": str(e)})
    
    return results
