import numpy as np

def check(fn):
    results = []
    np.random.seed(42)
    
    # Test 1: Periodicity invariance - adding integer translations to fractional coords
    # should give same result after wrapping
    try:
        N = 5
        X_prev = np.random.rand(N, 3) * 0.5  # Keep in [0, 0.5)
        score = np.random.randn(N, 3) * 0.1
        alpha = 0.01
        epsilon_noise = np.random.randn(N, 3)
        L = np.array([[3.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 5.0]])
        
        result1 = fn(X_prev, score, alpha, epsilon_noise, L)
        
        # Add integer offsets to X_prev (should wrap back to same result)
        X_prev_shifted = X_prev + np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 0.0], 
                                             [2.0, 0.0, 1.0], [1.0, 1.0, 1.0], 
                                             [0.0, 0.0, 2.0]])
        result2 = fn(X_prev_shifted, score, alpha, epsilon_noise, L)
        
        passed = np.allclose(result1, result2, atol=1e-6)
        results.append({
            "name": "periodicity_invariance",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result1 - result2))}" if not passed else "Integer shifts wrap correctly"
        })
    except Exception as e:
        results.append({"name": "periodicity_invariance", "passed": False, "detail": str(e)})
    
    # Test 2: Output bounds - all fractional coordinates must be in [0, 1)
    try:
        N = 10
        X_prev = np.random.rand(N, 3)
        score = np.random.randn(N, 3) * 0.5
        alpha = 0.05
        epsilon_noise = np.random.randn(N, 3)
        L = np.array([[4.0, 0.5, 0.0], [0.0, 3.5, 0.2], [0.0, 0.0, 5.0]])
        
        result = fn(X_prev, score, alpha, epsilon_noise, L)
        
        in_bounds = np.all(result >= 0.0) and np.all(result < 1.0)
        passed = in_bounds
        results.append({
            "name": "fractional_coordinate_bounds",
            "passed": passed,
            "detail": f"Min: {np.min(result)}, Max: {np.max(result)}" if not passed else "All coords in [0, 1)"
        })
    except Exception as e:
        results.append({"name": "fractional_coordinate_bounds", "passed": False, "detail": str(e)})
    
    # Test 3: Zero step size and zero noise - should return wrapped X_prev
    try:
        N = 4
        X_prev = np.array([[0.3, 0.7, 0.2], [1.5, 0.4, 2.8], [0.9, 0.1, 0.5], [-0.2, 0.6, 1.1]])
        score = np.random.randn(N, 3) * 10.0  # Large score shouldn't matter
        alpha = 0.0
        epsilon_noise = np.zeros((N, 3))
        L = np.array([[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]])
        
        result = fn(X_prev, score, alpha, epsilon_noise, L)
        
        # Expected: X_prev wrapped to [0, 1)
        expected = X_prev - np.floor(X_prev)
        
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "zero_step_identity",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result - expected))}" if not passed else "Zero step returns wrapped input"
        })
    except Exception as e:
        results.append({"name": "zero_step_identity", "passed": False, "detail": str(e)})
    
    # Test 4: Lattice scaling invariance - scaling lattice shouldn't affect fractional coords
    try:
        N = 6
        X_prev = np.random.rand(N, 3)
        score = np.random.randn(N, 3) * 0.1
        alpha = 0.02
        epsilon_noise = np.random.randn(N, 3)
        L1 = np.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]])
        L2 = L1 * 5.0  # Uniformly scaled lattice
        
        result1 = fn(X_prev, score, alpha, epsilon_noise, L1)
        result2 = fn(X_prev, score, alpha, epsilon_noise, L2)
        
        # Fractional coordinates should be identical regardless of lattice scale
        passed = np.allclose(result1, result2, atol=1e-6)
        results.append({
            "name": "lattice_scaling_invariance",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result1 - result2))}" if not passed else "Fractional coords invariant to lattice scaling"
        })
    except Exception as e:
        results.append({"name": "lattice_scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Deterministic update - same inputs give same outputs
    try:
        N = 7
        X_prev = np.random.rand(N, 3)
        score = np.random.randn(N, 3) * 0.2
        alpha = 0.03
        epsilon_noise = np.random.randn(N, 3)
        L = np.array([[3.5, 0.1, 0.0], [0.2, 4.0, 0.1], [0.0, 0.0, 5.5]])
        
        result1 = fn(X_prev.copy(), score.copy(), alpha, epsilon_noise.copy(), L.copy())
        result2 = fn(X_prev.copy(), score.copy(), alpha, epsilon_noise.copy(), L.copy())
        
        passed = np.allclose(result1, result2, atol=1e-10)
        results.append({
            "name": "deterministic_update",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result1 - result2))}" if not passed else "Deterministic behavior confirmed"
        })
    except Exception as e:
        results.append({"name": "deterministic_update", "passed": False, "detail": str(e)})
    
    return results
