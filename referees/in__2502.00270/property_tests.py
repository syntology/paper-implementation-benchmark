import numpy as np

def check(fn):
    results = []
    
    # Test 1: Element-wise correctness on small known input
    # Property: output[i] = mu_t[i] - beta_t * sigma_t[i] for all i
    try:
        mu_t = np.array([1.0, 2.0, 3.0])
        sigma_t = np.array([0.5, 0.2, 0.1])
        beta_t = 2.0
        output = fn(mu_t, sigma_t, beta_t)
        expected = np.array([1.0 - 2.0*0.5, 2.0 - 2.0*0.2, 3.0 - 2.0*0.1])
        passed = np.allclose(output, expected, atol=1e-6)
        results.append({
            "name": "element_wise_correctness",
            "passed": passed,
            "detail": f"output={output}, expected={expected}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "element_wise_correctness",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Zero exploration parameter (beta_t = 0)
    # Property: LCB should equal mu_t when beta_t = 0
    try:
        mu_t = np.array([1.5, -2.3, 0.0, 10.0])
        sigma_t = np.array([0.1, 0.5, 1.0, 2.0])
        beta_t = 0.0
        output = fn(mu_t, sigma_t, beta_t)
        expected = mu_t.copy()
        passed = np.allclose(output, expected, atol=1e-6)
        results.append({
            "name": "zero_beta_returns_mu",
            "passed": passed,
            "detail": f"output={output}, expected={expected}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "zero_beta_returns_mu",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Zero uncertainty (sigma_t = 0)
    # Property: LCB should equal mu_t when sigma_t = 0 (no uncertainty penalty)
    try:
        mu_t = np.array([5.0, -1.0, 0.0])
        sigma_t = np.array([0.0, 0.0, 0.0])
        beta_t = 10.0
        output = fn(mu_t, sigma_t, beta_t)
        expected = mu_t.copy()
        passed = np.allclose(output, expected, atol=1e-6)
        results.append({
            "name": "zero_sigma_returns_mu",
            "passed": passed,
            "detail": f"output={output}, expected={expected}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "zero_sigma_returns_mu",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Scaling property
    # Property: if beta_t increases, LCB decreases (more exploration penalty)
    try:
        mu_t = np.array([1.0, 2.0, 3.0])
        sigma_t = np.array([0.5, 0.5, 0.5])
        beta_t_1 = 1.0
        beta_t_2 = 2.0
        output_1 = fn(mu_t, sigma_t, beta_t_1)
        output_2 = fn(mu_t, sigma_t, beta_t_2)
        # All elements of output_2 should be <= output_1 (strictly less since sigma > 0)
        passed = np.all(output_2 < output_1)
        results.append({
            "name": "increasing_beta_decreases_lcb",
            "passed": passed,
            "detail": f"output_1={output_1}, output_2={output_2}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "increasing_beta_decreases_lcb",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Output shape and type preservation
    # Property: output shape matches input shape, output is numpy array
    try:
        for n in [1, 5, 100]:
            mu_t = np.random.randn(n)
            sigma_t = np.abs(np.random.randn(n))
            beta_t = np.abs(np.random.randn())
            output = fn(mu_t, sigma_t, beta_t)
            shape_match = output.shape == (n,)
            is_ndarray = isinstance(output, np.ndarray)
            if not (shape_match and is_ndarray):
                raise AssertionError(f"n={n}: shape={output.shape}, type={type(output)}")
        results.append({
            "name": "output_shape_and_type",
            "passed": True,
            "detail": "OK"
        })
    except Exception as e:
        results.append({
            "name": "output_shape_and_type",
            "passed": False,
            "detail": str(e)
        })
    
    return results
