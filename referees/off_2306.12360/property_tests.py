import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape matches input shape
    try:
        d = 5
        y_t = np.random.RandomState(42).randn(d)
        grad_f = np.random.RandomState(43).randn(d)
        epsilon_t = np.random.RandomState(44).randn(d)
        delta = 0.01
        
        y_next = fn(y_t, grad_f, epsilon_t, delta)
        
        passed = y_next.shape == (d,) and isinstance(y_next, np.ndarray)
        detail = f"Output shape {y_next.shape}, expected ({d},)" if not passed else "Shape correct"
        results.append({"name": "output_shape_matches_input", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_matches_input", "passed": False, "detail": str(e)})
    
    # Test 2: Zero gradient and zero noise recovers pure drift
    try:
        d = 4
        y_t = np.array([1.0, 2.0, 3.0, 4.0])
        grad_f = np.array([0.5, 0.2, -0.3, 0.1])
        epsilon_t = np.zeros(d)  # No noise
        delta = 0.1
        
        y_next = fn(y_t, grad_f, epsilon_t, delta)
        expected = y_t - delta * grad_f
        
        passed = np.allclose(y_next, expected, atol=1e-6)
        detail = f"Max diff: {np.max(np.abs(y_next - expected))}" if not passed else "Drift term correct"
        results.append({"name": "zero_noise_recovers_drift", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_noise_recovers_drift", "passed": False, "detail": str(e)})
    
    # Test 3: Zero gradient with noise recovers pure diffusion
    try:
        d = 3
        y_t = np.array([1.0, -1.0, 0.5])
        grad_f = np.zeros(d)  # No drift
        epsilon_t = np.array([1.0, 2.0, -1.0])
        delta = 0.04
        
        y_next = fn(y_t, grad_f, epsilon_t, delta)
        expected = y_t + np.sqrt(2 * delta) * epsilon_t
        
        passed = np.allclose(y_next, expected, atol=1e-6)
        detail = f"Max diff: {np.max(np.abs(y_next - expected))}" if not passed else "Diffusion term correct"
        results.append({"name": "zero_gradient_recovers_diffusion", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_gradient_recovers_diffusion", "passed": False, "detail": str(e)})
    
    # Test 4: Linearity in gradient (negative sign convention)
    try:
        d = 3
        y_t = np.array([0.5, -0.5, 1.0])
        grad_f = np.array([0.2, 0.3, -0.1])
        epsilon_t = np.array([0.0, 0.0, 0.0])
        delta = 0.05
        
        y_next_pos = fn(y_t, grad_f, epsilon_t, delta)
        y_next_neg = fn(y_t, -grad_f, epsilon_t, delta)
        
        # Flipping gradient sign should flip the drift direction
        expected_diff = 2 * delta * grad_f
        actual_diff = y_next_neg - y_next_pos
        
        passed = np.allclose(actual_diff, expected_diff, atol=1e-6)
        detail = f"Max diff: {np.max(np.abs(actual_diff - expected_diff))}" if not passed else "Gradient linearity correct"
        results.append({"name": "gradient_linearity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "gradient_linearity", "passed": False, "detail": str(e)})
    
    # Test 5: Scaling invariance in step size (deterministic component)
    try:
        d = 3
        y_t = np.array([1.0, 2.0, 3.0])
        grad_f = np.array([0.1, -0.2, 0.3])
        epsilon_t = np.zeros(d)  # Deterministic test
        delta1 = 0.01
        delta2 = 0.02
        
        y_next_1 = fn(y_t, grad_f, epsilon_t, delta1)
        y_next_2 = fn(y_t, grad_f, epsilon_t, delta2)
        
        # Larger step should move further in same direction
        diff_1 = y_next_1 - y_t
        diff_2 = y_next_2 - y_t
        
        # diff_2 should be 2x diff_1 (since delta2 = 2*delta1)
        ratio = diff_2 / (diff_1 + 1e-10)
        expected_ratio = 2.0
        
        passed = np.allclose(ratio, expected_ratio, atol=1e-6)
        detail = f"Ratio: {np.mean(ratio)}, expected {expected_ratio}" if not passed else "Step size scaling correct"
        results.append({"name": "step_size_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "step_size_scaling", "passed": False, "detail": str(e)})
    
    return results
