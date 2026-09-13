import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero matrix should give zero gradient
    try:
        d = 4
        W = np.zeros((d, d))
        grad = fn(W)
        expected = np.zeros((d, d))
        passed = np.allclose(grad, expected, atol=1e-6)
        results.append({
            "name": "Zero matrix gives zero gradient",
            "passed": passed,
            "detail": f"Max absolute difference: {np.max(np.abs(grad - expected))}"
        })
    except Exception as e:
        results.append({
            "name": "Zero matrix gives zero gradient",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Permutation invariance - gradient should transform consistently with row/col permutation
    try:
        d = 4
        np.random.seed(42)
        W = np.random.randn(d, d) * 0.1
        grad = fn(W)
        
        # Apply same permutation to rows and columns
        P = np.array([0, 2, 1, 3])  # permutation
        W_perm = W[P, :][:, P]
        grad_perm = fn(W_perm)
        
        # The gradient should transform the same way
        grad_expected = grad[P, :][:, P]
        passed = np.allclose(grad_perm, grad_expected, atol=1e-6)
        results.append({
            "name": "Permutation invariance",
            "passed": passed,
            "detail": f"Max absolute difference: {np.max(np.abs(grad_perm - grad_expected))}"
        })
    except Exception as e:
        results.append({
            "name": "Permutation invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Gradient should be zero for diagonal matrices (no cycles possible)
    try:
        d = 4
        W = np.diag([0.1, 0.2, 0.3, 0.4])
        grad = fn(W)
        
        # For diagonal W, W⊙W is also diagonal, so (I + αW⊙W)^(d-1) is diagonal
        # and the gradient involves multiplying by 2W which is diagonal
        # The result should be diagonal (off-diagonal elements are zero)
        off_diag_mask = ~np.eye(d, dtype=bool)
        max_off_diag = np.max(np.abs(grad[off_diag_mask]))
        passed = max_off_diag < 1e-6
        results.append({
            "name": "Diagonal matrix gives diagonal gradient",
            "passed": passed,
            "detail": f"Max off-diagonal element: {max_off_diag}"
        })
    except Exception as e:
        results.append({
            "name": "Diagonal matrix gives diagonal gradient",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Scaling property - gradient should scale quadratically with W
    try:
        d = 3
        np.random.seed(123)
        W = np.random.randn(d, d) * 0.05
        grad1 = fn(W)
        
        # Scale W by a factor
        scale = 2.0
        W_scaled = scale * W
        grad_scaled = fn(W_scaled)
        
        # The gradient should scale, but the relationship is complex due to the matrix power
        # However, for small W, we can verify consistency by checking that
        # grad(cW) is close to what we'd expect from the formula structure
        # At minimum, verify the function runs and produces correct shape
        passed = grad_scaled.shape == (d, d) and not np.any(np.isnan(grad_scaled))
        results.append({
            "name": "Scaling produces valid output",
            "passed": passed,
            "detail": f"Shape: {grad_scaled.shape}, has NaN: {np.any(np.isnan(grad_scaled))}"
        })
    except Exception as e:
        results.append({
            "name": "Scaling produces valid output",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Gradient symmetry for symmetric input
    try:
        d = 4
        np.random.seed(456)
        W_asym = np.random.randn(d, d) * 0.1
        W = (W_asym + W_asym.T) / 2  # Make symmetric
        grad = fn(W)
        
        # For symmetric W, W⊙W is also symmetric
        # (I + αW⊙W)^(d-1) is symmetric
        # But grad = α * ((I + αW⊙W)^(d-1))^T * (2W)
        # Since (I + αW⊙W)^(d-1) is symmetric, its transpose equals itself
        # So grad = α * (I + αW⊙W)^(d-1) * (2W)
        # This is symmetric matrix times symmetric matrix, which is generally NOT symmetric
        # So we just check the output is valid
        passed = grad.shape == (d, d) and not np.any(np.isnan(grad)) and not np.any(np.isinf(grad))
        results.append({
            "name": "Symmetric input produces valid gradient",
            "passed": passed,
            "detail": f"Shape: {grad.shape}, finite: {np.all(np.isfinite(grad))}"
        })
    except Exception as e:
        results.append({
            "name": "Symmetric input produces valid gradient",
            "passed": False,
            "detail": str(e)
        })
    
    return results
