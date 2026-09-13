import numpy as np

def check(fn):
    results = []
    
    # Test 1: Limiting case rho=1 (target params unchanged)
    try:
        target = np.array([[1.0, 2.0], [3.0, 4.0]])
        online = np.array([[5.0, 6.0], [7.0, 8.0]])
        rho = 1.0
        result = fn(target, online, rho)
        expected = target
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"rho=1: result={result.tolist()}, expected={expected.tolist()}"
        results.append({"name": "limiting_case_rho_1", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "limiting_case_rho_1", "passed": False, "detail": str(e)})
    
    # Test 2: Limiting case rho=0 (target becomes online)
    try:
        target = np.array([[1.0, 2.0], [3.0, 4.0]])
        online = np.array([[5.0, 6.0], [7.0, 8.0]])
        rho = 0.0
        result = fn(target, online, rho)
        expected = online
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"rho=0: result={result.tolist()}, expected={expected.tolist()}"
        results.append({"name": "limiting_case_rho_0", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "limiting_case_rho_0", "passed": False, "detail": str(e)})
    
    # Test 3: Convex combination property (result lies between target and online)
    try:
        target = np.array([1.0, 2.0, 3.0])
        online = np.array([5.0, 6.0, 7.0])
        rho = 0.3
        result = fn(target, online, rho)
        # For each element, result should be between target and online
        min_vals = np.minimum(target, online)
        max_vals = np.maximum(target, online)
        in_bounds = np.all((result >= min_vals - 1e-6) & (result <= max_vals + 1e-6))
        passed = in_bounds
        detail = f"rho={rho}: result={result.tolist()}, target={target.tolist()}, online={online.tolist()}, in_bounds={in_bounds}"
        results.append({"name": "convex_combination_bounds", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "convex_combination_bounds", "passed": False, "detail": str(e)})
    
    # Test 4: Affine property - when target=online, result equals both
    try:
        params = np.array([[2.5, -1.0], [0.0, 3.7]])
        rho = 0.6
        result = fn(params, params, rho)
        expected = params
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"target=online: result={result.tolist()}, expected={expected.tolist()}"
        results.append({"name": "identical_params_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identical_params_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Linear interpolation property - explicit formula verification
    try:
        target = np.array([[[1.0, 2.0]], [[3.0, 4.0]]])
        online = np.array([[[10.0, 20.0]], [[30.0, 40.0]]])
        rho = 0.25
        result = fn(target, online, rho)
        expected = rho * target + (1 - rho) * online
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"3D array, rho={rho}: max_diff={np.max(np.abs(result - expected))}"
        results.append({"name": "explicit_formula_verification", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "explicit_formula_verification", "passed": False, "detail": str(e)})
    
    return results
