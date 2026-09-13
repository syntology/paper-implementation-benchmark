import numpy as np

def check(fn):
    results = []
    
    # Test 1: Scaling invariance of direction vector
    # If we scale (h_test - h_baseline) by a positive constant, the direction vector v
    # changes but the final result should remain the same because v is normalized by ||h_test - h_baseline||_2^2
    try:
        np.random.seed(42)
        d_X, d_H, C, n_bins = 3, 4, 5, 10
        x_test = np.random.randn(d_X)
        x_corpus = np.random.randn(C, d_X)
        x_baseline = np.random.randn(d_X)
        h_baseline = np.random.randn(d_H)
        h_test_base = np.random.randn(d_H)
        h_test_base = h_baseline + (h_test_base - h_baseline) * 0.5  # ensure different from baseline
        jacobian_g = np.random.randn(C, n_bins, d_H, d_X) * 0.1
        
        P1 = fn(x_test, h_test_base, x_corpus, h_corpus := np.random.randn(C, d_H), 
                x_baseline, h_baseline, jacobian_g, n_bins)
        
        scale = 3.7
        h_test_scaled = h_baseline + scale * (h_test_base - h_baseline)
        P2 = fn(x_test, h_test_scaled, x_corpus, h_corpus, 
                x_baseline, h_baseline, jacobian_g, n_bins)
        
        passed = np.allclose(P1, P2, atol=1e-6)
        results.append({
            "name": "scaling_invariance_h_test",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(P1 - P2))}" if not passed else "P invariant under scaling of (h_test - h_baseline)"
        })
    except Exception as e:
        results.append({"name": "scaling_invariance_h_test", "passed": False, "detail": str(e)})
    
    # Test 2: Zero Jacobian implies zero projection
    # If all Jacobians are zero, then P should be zero regardless of inputs
    try:
        np.random.seed(43)
        d_X, d_H, C, n_bins = 3, 4, 5, 10
        x_test = np.random.randn(d_X)
        h_test = np.random.randn(d_H)
        x_corpus = np.random.randn(C, d_X)
        h_corpus = np.random.randn(C, d_H)
        x_baseline = np.random.randn(d_X)
        h_baseline = np.random.randn(d_H)
        jacobian_g = np.zeros((C, n_bins, d_H, d_X))
        
        P = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g, n_bins)
        
        passed = np.allclose(P, 0.0, atol=1e-6)
        results.append({
            "name": "zero_jacobian_zero_projection",
            "passed": passed,
            "detail": f"max abs value: {np.max(np.abs(P))}" if not passed else "P is zero when all Jacobians are zero"
        })
    except Exception as e:
        results.append({"name": "zero_jacobian_zero_projection", "passed": False, "detail": str(e)})
    
    # Test 3: When x_corpus equals x_baseline (broadcasted), the final multiplication makes P zero
    # Because (x_corpus - X^0) = 0, the element-wise product in step 4 yields zero
    try:
        np.random.seed(44)
        d_X, d_H, C, n_bins = 3, 4, 5, 10
        x_test = np.random.randn(d_X)
        h_test = np.random.randn(d_H)
        x_baseline = np.random.randn(d_X)
        x_corpus = np.tile(x_baseline, (C, 1))  # All corpus examples equal baseline
        h_corpus = np.random.randn(C, d_H)
        h_baseline = np.random.randn(d_H)
        jacobian_g = np.random.randn(C, n_bins, d_H, d_X) * 0.1
        
        P = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g, n_bins)
        
        passed = np.allclose(P, 0.0, atol=1e-6)
        results.append({
            "name": "corpus_equals_baseline_zero_projection",
            "passed": passed,
            "detail": f"max abs value: {np.max(np.abs(P))}" if not passed else "P is zero when x_corpus equals x_baseline"
        })
    except Exception as e:
        results.append({"name": "corpus_equals_baseline_zero_projection", "passed": False, "detail": str(e)})
    
    # Test 4: Output shape and dtype
    # P must have shape (C, d_X) and dtype float64
    try:
        np.random.seed(45)
        d_X, d_H, C, n_bins = 3, 4, 5, 10
        x_test = np.random.randn(d_X)
        h_test = np.random.randn(d_H)
        x_corpus = np.random.randn(C, d_X)
        h_corpus = np.random.randn(C, d_H)
        x_baseline = np.random.randn(d_X)
        h_baseline = np.random.randn(d_H)
        jacobian_g = np.random.randn(C, n_bins, d_H, d_X) * 0.1
        
        P = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g, n_bins)
        
        shape_correct = P.shape == (C, d_X)
        dtype_correct = P.dtype == np.float64
        passed = shape_correct and dtype_correct
        
        results.append({
            "name": "output_shape_and_dtype",
            "passed": passed,
            "detail": f"shape: {P.shape} (expected {(C, d_X)}), dtype: {P.dtype} (expected float64)" if not passed else "Correct shape and dtype"
        })
    except Exception as e:
        results.append({"name": "output_shape_and_dtype", "passed": False, "detail": str(e)})
    
    # Test 5: Linear scaling with (1/n_bins) factor
    # If we double n_bins and double the jacobian values, the contribution per bin should balance
    # More precisely: P scales as 1/n_bins from the final multiplication
    try:
        np.random.seed(46)
        d_X, d_H, C = 3, 4, 5
        x_test = np.random.randn(d_X)
        h_test = np.random.randn(d_H)
        x_corpus = np.random.randn(C, d_X)
        h_corpus = np.random.randn(C, d_H)
        x_baseline = np.random.randn(d_X)
        h_baseline = np.random.randn(d_H)
        
        n_bins_1 = 10
        jacobian_g_1 = np.random.randn(C, n_bins_1, d_H, d_X) * 0.1
        P1 = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g_1, n_bins_1)
        
        n_bins_2 = 20
        # For the same continuous function, doubling bins means each jacobian contributes half as much in the sum
        # but we have twice as many bins, so we need to keep jacobian values the same
        jacobian_g_2 = np.random.randn(C, n_bins_2, d_H, d_X) * 0.1
        P2 = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g_2, n_bins_2)
        
        # This test checks that P scales with 1/n_bins when jacobians are scaled by n_bins
        jacobian_g_2_scaled = np.tile(jacobian_g_1, (1, 2, 1, 1))[:, :n_bins_2, :, :] * 2
        P2_scaled = fn(x_test, h_test, x_corpus, h_corpus, x_baseline, h_baseline, jacobian_g_2_scaled, n_bins_2)
        
        passed = np.allclose(P1, P2_scaled, atol=1e-6)
        results.append({
            "name": "n_bins_scaling_property",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(P1 - P2_scaled))}" if not passed else "Correct scaling with n_bins and jacobian values"
        })
    except Exception as e:
        results.append({"name": "n_bins_scaling_property", "passed": False, "detail": str(e)})
    
    return results
