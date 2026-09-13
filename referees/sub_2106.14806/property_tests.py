import numpy as np

def check(fn):
    results = []
    
    # Test 1: Permutation invariance - gradient should be invariant to permutation of hessian_diag
    try:
        np.random.seed(42)
        hessian_diag = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        prior_precision = 2.0
        n_data = 100
        
        grad1 = fn(hessian_diag, prior_precision, n_data)
        
        # Permute the hessian_diag
        permuted = np.array([5.0, 2.0, 4.0, 1.0, 3.0])
        grad2 = fn(permuted, prior_precision, n_data)
        
        passed = np.abs(grad1 - grad2) < 1e-6
        results.append({
            "name": "permutation_invariance",
            "passed": bool(passed),
            "detail": f"Original grad: {grad1}, Permuted grad: {grad2}, diff: {np.abs(grad1 - grad2)}"
        })
    except Exception as e:
        results.append({
            "name": "permutation_invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Limiting case - as prior_precision -> infinity, gradient should approach 0.5 * n_params / prior_precision
    try:
        np.random.seed(42)
        hessian_diag = np.array([1.0, 2.0, 3.0])
        n_params = len(hessian_diag)
        n_data = 100
        prior_precision = 1e6  # Very large
        
        grad = fn(hessian_diag, prior_precision, n_data)
        
        # When prior_precision >> hessian_diag, the first term -0.5 * sum(1/(hessian_diag + prior_precision))
        # approaches -0.5 * n_params / prior_precision
        # So total gradient approaches: -0.5 * n_params / prior_precision + 0.5 * n_params / prior_precision = 0
        expected_grad = 0.0
        
        passed = np.abs(grad - expected_grad) < 1e-3  # Looser tolerance for limiting case
        results.append({
            "name": "limiting_case_large_prior_precision",
            "passed": bool(passed),
            "detail": f"Grad at large prior_precision: {grad}, Expected: {expected_grad}, diff: {np.abs(grad - expected_grad)}"
        })
    except Exception as e:
        results.append({
            "name": "limiting_case_large_prior_precision",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Uniform hessian case - closed form verification
    try:
        # When all hessian_diag elements are equal to h, we have:
        # gradient = -0.5 * n_params / (h + prior_precision) + 0.5 * n_params / prior_precision
        h = 3.0
        n_params = 5
        hessian_diag = np.full(n_params, h)
        prior_precision = 2.0
        n_data = 100
        
        grad = fn(hessian_diag, prior_precision, n_data)
        expected_grad = -0.5 * n_params / (h + prior_precision) + 0.5 * n_params / prior_precision
        
        passed = np.abs(grad - expected_grad) < 1e-6
        results.append({
            "name": "uniform_hessian_closed_form",
            "passed": bool(passed),
            "detail": f"Grad: {grad}, Expected: {expected_grad}, diff: {np.abs(grad - expected_grad)}"
        })
    except Exception as e:
        results.append({
            "name": "uniform_hessian_closed_form",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Scaling property - scaling all hessian_diag by constant and prior_precision by same constant
    try:
        np.random.seed(42)
        hessian_diag = np.array([1.0, 2.0, 3.0, 4.0])
        prior_precision = 2.0
        n_data = 100
        scale = 5.0
        
        grad1 = fn(hessian_diag, prior_precision, n_data)
        grad2 = fn(scale * hessian_diag, scale * prior_precision, n_data)
        
        # When both hessian_diag and prior_precision are scaled by c:
        # gradient = -0.5 * sum(1/(c*h_i + c*p)) + 0.5 * n_params / (c*p)
        #          = -0.5 * sum(1/(c*(h_i + p))) + 0.5 * n_params / (c*p)
        #          = -0.5/(c) * sum(1/(h_i + p)) + 0.5/(c) * n_params / p
        #          = (1/c) * original_gradient
        expected_grad2 = grad1 / scale
        
        passed = np.abs(grad2 - expected_grad2) < 1e-6
        results.append({
            "name": "uniform_scaling_property",
            "passed": bool(passed),
            "detail": f"Original grad: {grad1}, Scaled grad: {grad2}, Expected scaled: {expected_grad2}, diff: {np.abs(grad2 - expected_grad2)}"
        })
    except Exception as e:
        results.append({
            "name": "uniform_scaling_property",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Single parameter case - exact closed form
    try:
        hessian_diag = np.array([4.0])
        prior_precision = 3.0
        n_data = 100
        
        grad = fn(hessian_diag, prior_precision, n_data)
        # For single parameter: gradient = -0.5 / (4.0 + 3.0) + 0.5 / 3.0
        expected_grad = -0.5 / (4.0 + 3.0) + 0.5 / 3.0
        
        passed = np.abs(grad - expected_grad) < 1e-6
        results.append({
            "name": "single_parameter_exact",
            "passed": bool(passed),
            "detail": f"Grad: {grad}, Expected: {expected_grad}, diff: {np.abs(grad - expected_grad)}"
        })
    except Exception as e:
        results.append({
            "name": "single_parameter_exact",
            "passed": False,
            "detail": str(e)
        })
    
    return results
