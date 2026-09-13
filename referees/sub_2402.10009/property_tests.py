import numpy as np

def check(fn):
    results = []
    
    # Test 1: Linearity in f_t_x_t_shifted
    # Property: x0_prediction is linear in the denoiser output.
    # If we scale f_t by a constant c, the output should scale by -c*sqrt(1-alpha_bar_t)/sqrt(alpha_bar_t)
    try:
        np.random.seed(42)
        D = 5
        x_t = np.random.randn(D)
        f_t_1 = np.random.randn(D)
        alpha_bar_t = 0.7
        
        x0_1 = fn(x_t, f_t_1, alpha_bar_t)
        
        # Scale f_t by 2
        f_t_2 = 2.0 * f_t_1
        x0_2 = fn(x_t, f_t_2, alpha_bar_t)
        
        # Expected: x0_2 - x0_1 = -2*sqrt(1-alpha_bar_t)/sqrt(alpha_bar_t) * f_t_1
        scale_factor = -np.sqrt(1 - alpha_bar_t) / np.sqrt(alpha_bar_t)
        expected_diff = scale_factor * f_t_1
        actual_diff = x0_2 - x0_1
        
        passed = np.allclose(actual_diff, expected_diff, atol=1e-6)
        results.append({
            "name": "Linearity in denoiser output",
            "passed": passed,
            "detail": f"max error: {np.max(np.abs(actual_diff - expected_diff))}"
        })
    except Exception as e:
        results.append({
            "name": "Linearity in denoiser output",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Limiting case alpha_bar_t -> 1 (clean signal)
    # Property: As alpha_bar_t approaches 1, the noise term vanishes and x0 should approach x_t
    try:
        np.random.seed(43)
        D = 5
        x_t = np.random.randn(D)
        f_t = np.random.randn(D)
        alpha_bar_t = 0.9999  # Very close to 1
        
        x0 = fn(x_t, f_t, alpha_bar_t)
        
        # When alpha_bar_t ≈ 1: x0 ≈ x_t / 1 - sqrt(1-1)*f_t/1 ≈ x_t
        passed = np.allclose(x0, x_t, atol=1e-3)
        results.append({
            "name": "Limiting case: alpha_bar_t → 1",
            "passed": passed,
            "detail": f"max error: {np.max(np.abs(x0 - x_t))}"
        })
    except Exception as e:
        results.append({
            "name": "Limiting case: alpha_bar_t → 1",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Zero denoiser output case
    # Property: When f_t(x_t_shifted) = 0 (perfect denoiser), x0 = x_t / sqrt(alpha_bar_t)
    try:
        np.random.seed(44)
        D = 5
        x_t = np.random.randn(D)
        f_t = np.zeros(D)  # Perfect denoiser output
        alpha_bar_t = 0.5
        
        x0 = fn(x_t, f_t, alpha_bar_t)
        expected_x0 = x_t / np.sqrt(alpha_bar_t)
        
        passed = np.allclose(x0, expected_x0, atol=1e-6)
        results.append({
            "name": "Zero denoiser output",
            "passed": passed,
            "detail": f"max error: {np.max(np.abs(x0 - expected_x0))}"
        })
    except Exception as e:
        results.append({
            "name": "Zero denoiser output",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Permutation invariance
    # Property: Permuting elements of x_t and f_t consistently should permute the output
    try:
        np.random.seed(45)
        D = 5
        x_t = np.random.randn(D)
        f_t = np.random.randn(D)
        alpha_bar_t = 0.6
        
        x0 = fn(x_t, f_t, alpha_bar_t)
        
        # Permute indices
        perm = np.array([2, 0, 4, 1, 3])
        x_t_perm = x_t[perm]
        f_t_perm = f_t[perm]
        
        x0_perm = fn(x_t_perm, f_t_perm, alpha_bar_t)
        x0_perm_expected = x0[perm]
        
        passed = np.allclose(x0_perm, x0_perm_expected, atol=1e-6)
        results.append({
            "name": "Permutation invariance",
            "passed": passed,
            "detail": f"max error: {np.max(np.abs(x0_perm - x0_perm_expected))}"
        })
    except Exception as e:
        results.append({
            "name": "Permutation invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Scaling property with alpha_bar_t
    # Property: The output scales inversely with sqrt(alpha_bar_t) when x_t and f_t are fixed
    try:
        np.random.seed(46)
        D = 5
        x_t = np.random.randn(D)
        f_t = np.random.randn(D)
        
        alpha_bar_t_1 = 0.4
        alpha_bar_t_2 = 0.9
        
        x0_1 = fn(x_t, f_t, alpha_bar_t_1)
        x0_2 = fn(x_t, f_t, alpha_bar_t_2)
        
        # Ratio should be sqrt(alpha_bar_t_2) / sqrt(alpha_bar_t_1)
        expected_ratio = np.sqrt(alpha_bar_t_2) / np.sqrt(alpha_bar_t_1)
        actual_ratio = x0_2 / x0_1  # Element-wise
        
        passed = np.allclose(actual_ratio, expected_ratio, atol=1e-6)
        results.append({
            "name": "Scaling with alpha_bar_t",
            "passed": passed,
            "detail": f"max error in ratio: {np.max(np.abs(actual_ratio - expected_ratio))}"
        })
    except Exception as e:
        results.append({
            "name": "Scaling with alpha_bar_t",
            "passed": False,
            "detail": str(e)
        })
    
    return results
