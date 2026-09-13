import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output bounds - quantized values must be in [quant_min, quant_max]
    try:
        np.random.seed(42)
        d_row, d_col = 4, 8
        B = 4
        quant_min, quant_max = -3.0, 3.0
        
        W = np.random.randn(d_row, d_col).astype(np.float64)
        H = np.random.randn(d_col, d_col)
        H_inv = np.dot(H.T, H) + np.eye(d_col)  # SPD matrix
        
        Q = fn(W.copy(), H_inv.copy(), B, quant_min, quant_max)
        
        within_bounds = np.all((Q >= quant_min - 1e-9) & (Q <= quant_max + 1e-9))
        all_integers = np.allclose(Q, np.round(Q), atol=1e-9)
        
        passed = within_bounds and all_integers
        detail = f"Within bounds: {within_bounds}, All integers: {all_integers}, min={Q.min()}, max={Q.max()}"
        results.append({"name": "output_bounds", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_bounds", "passed": False, "detail": str(e)})
    
    # Test 2: Uniform scaling - scaling W by constant c scales Q by c (when no clipping occurs)
    try:
        np.random.seed(43)
        d_row, d_col = 3, 6
        B = 3
        quant_min, quant_max = -100.0, 100.0  # Large range to avoid clipping
        
        W = 0.1 * np.random.randn(d_row, d_col).astype(np.float64)  # Small values
        H = np.random.randn(d_col, d_col)
        H_inv = np.dot(H.T, H) + np.eye(d_col)
        
        scale = 2.0
        Q1 = fn(W.copy(), H_inv.copy(), B, quant_min, quant_max)
        Q2 = fn((scale * W).copy(), H_inv.copy(), B, quant_min, quant_max)
        
        passed = np.allclose(Q2, scale * Q1, atol=1e-6)
        detail = f"Max difference: {np.max(np.abs(Q2 - scale * Q1))}"
        results.append({"name": "uniform_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "uniform_scaling", "passed": False, "detail": str(e)})
    
    # Test 3: Degenerate case - H_inv = identity, B = 1 should give simple rounding
    try:
        np.random.seed(44)
        d_row, d_col = 3, 4
        B = 1
        quant_min, quant_max = -10.0, 10.0
        
        W = np.random.randn(d_row, d_col).astype(np.float64)
        H_inv = np.eye(d_col, dtype=np.float64)
        
        Q = fn(W.copy(), H_inv.copy(), B, quant_min, quant_max)
        expected = np.clip(np.round(W), quant_min, quant_max)
        
        passed = np.allclose(Q, expected, atol=1e-9)
        detail = f"Max difference from simple rounding: {np.max(np.abs(Q - expected))}"
        results.append({"name": "identity_hessian", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identity_hessian", "passed": False, "detail": str(e)})
    
    # Test 4: Column permutation invariance - permuting columns of W and H_inv consistently
    try:
        np.random.seed(45)
        d_row, d_col = 4, 8
        B = 4
        quant_min, quant_max = -5.0, 5.0
        
        W = np.random.randn(d_row, d_col).astype(np.float64)
        H = np.random.randn(d_col, d_col)
        H_inv = np.dot(H.T, H) + np.eye(d_col)
        
        # Permutation that respects block boundaries
        perm = np.array([0, 1, 2, 3, 4, 5, 6, 7])
        perm[:4] = [1, 0, 3, 2]  # Permute within first block
        perm[4:] = [5, 4, 7, 6]  # Permute within second block
        
        Q1 = fn(W.copy(), H_inv.copy(), B, quant_min, quant_max)
        
        W_perm = W[:, perm]
        H_inv_perm = H_inv[np.ix_(perm, perm)]
        Q2 = fn(W_perm.copy(), H_inv_perm.copy(), B, quant_min, quant_max)
        
        # Q2 should be Q1 with columns permuted
        Q1_perm = Q1[:, perm]
        passed = np.allclose(Q2, Q1_perm, atol=1e-6)
        detail = f"Max difference: {np.max(np.abs(Q2 - Q1_perm))}"
        results.append({"name": "block_column_permutation", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "block_column_permutation", "passed": False, "detail": str(e)})
    
    # Test 5: Zero weight matrix should return zero quantized matrix
    try:
        np.random.seed(46)
        d_row, d_col = 3, 6
        B = 2
        quant_min, quant_max = -5.0, 5.0
        
        W = np.zeros((d_row, d_col), dtype=np.float64)
        H = np.random.randn(d_col, d_col)
        H_inv = np.dot(H.T, H) + np.eye(d_col)
        
        Q = fn(W.copy(), H_inv.copy(), B, quant_min, quant_max)
        
        passed = np.allclose(Q, 0.0, atol=1e-9)
        detail = f"Max absolute value: {np.max(np.abs(Q))}"
        results.append({"name": "zero_weight", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_weight", "passed": False, "detail": str(e)})
    
    return results
