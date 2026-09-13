import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape is always (E,)
    try:
        np.random.seed(42)
        E, C, D = 5, 3, 10
        x = np.random.randn(D)
        phi_B = np.random.randn(E)
        omega_r = np.random.randn(C, E)
        mask = np.random.rand(E) > 0.5
        
        output = fn(x, phi_B, omega_r, mask)
        
        assert isinstance(output, np.ndarray), f"Output is not ndarray, got {type(output)}"
        assert output.shape == (E,), f"Output shape is {output.shape}, expected ({E},)"
        assert output.dtype in [np.float32, np.float64], f"Output dtype {output.dtype} is not float"
        
        results.append({
            "name": "output_shape_and_dtype",
            "passed": True,
            "detail": f"Output shape {output.shape} and dtype {output.dtype} correct"
        })
    except Exception as e:
        results.append({
            "name": "output_shape_and_dtype",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Masked positions are exactly zero
    try:
        np.random.seed(43)
        E, C, D = 8, 2, 12
        x = np.random.randn(D)
        phi_B = np.random.randn(E)
        omega_r = np.random.randn(C, E)
        mask = np.array([True, False, True, False, True, False, True, False])
        
        output = fn(x, phi_B, omega_r, mask)
        
        # Where mask is False, output must be exactly 0
        masked_out_positions = output[~mask]
        assert np.allclose(masked_out_positions, 0.0, atol=1e-15), \
            f"Masked positions not zero: {masked_out_positions}"
        
        results.append({
            "name": "masked_positions_zero",
            "passed": True,
            "detail": "All masked-out positions are exactly zero"
        })
    except Exception as e:
        results.append({
            "name": "masked_positions_zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Unmasked output equals omega_r[0, :] * mask * phi_B (element-wise)
    try:
        np.random.seed(44)
        E, C, D = 6, 4, 8
        x = np.random.randn(D)
        phi_B = np.random.randn(E)
        omega_r = np.random.randn(C, E)
        mask = np.array([True, True, False, True, False, False])
        
        output = fn(x, phi_B, omega_r, mask)
        
        # Expected: gradient = omega_r[0, :], masked_grad = gradient * mask.astype(float)
        expected_gradient = omega_r[0, :]
        expected_output = expected_gradient * mask.astype(float)
        
        assert np.allclose(output, expected_output, atol=1e-6), \
            f"Output {output} != expected {expected_output}"
        
        results.append({
            "name": "gradient_masking_correctness",
            "passed": True,
            "detail": "Output matches omega_r[0, :] * mask element-wise"
        })
    except Exception as e:
        results.append({
            "name": "gradient_masking_correctness",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: All-True mask returns omega_r[0, :] exactly
    try:
        np.random.seed(45)
        E, C, D = 7, 3, 9
        x = np.random.randn(D)
        phi_B = np.random.randn(E)
        omega_r = np.random.randn(C, E)
        mask = np.ones(E, dtype=bool)
        
        output = fn(x, phi_B, omega_r, mask)
        expected = omega_r[0, :]
        
        assert np.allclose(output, expected, atol=1e-6), \
            f"All-True mask output {output} != omega_r[0, :] {expected}"
        
        results.append({
            "name": "all_true_mask_identity",
            "passed": True,
            "detail": "All-True mask returns omega_r[0, :] exactly"
        })
    except Exception as e:
        results.append({
            "name": "all_true_mask_identity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: All-False mask returns zero vector
    try:
        np.random.seed(46)
        E, C, D = 5, 2, 10
        x = np.random.randn(D)
        phi_B = np.random.randn(E)
        omega_r = np.random.randn(C, E)
        mask = np.zeros(E, dtype=bool)
        
        output = fn(x, phi_B, omega_r, mask)
        expected = np.zeros(E)
        
        assert np.allclose(output, expected, atol=1e-15), \
            f"All-False mask output {output} != zero vector"
        
        results.append({
            "name": "all_false_mask_zero",
            "passed": True,
            "detail": "All-False mask returns zero vector"
        })
    except Exception as e:
        results.append({
            "name": "all_false_mask_zero",
            "passed": False,
            "detail": str(e)
        })
    
    return results
