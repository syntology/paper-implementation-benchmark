import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero step size should return eps_hat unchanged
    # When eps_step_size = 0, decay factor = 1, step_weights all = 1, weighted_noises all = 0
    try:
        np.random.seed(42)
        B, D = 2, 3
        eps_hat = np.random.randn(B, D)
        eps_init = np.random.randn(B, D)
        eps_noises = np.random.randn(5, B, D)
        eps_step_size = 0.0
        ld_steps = 5
        
        result = fn(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps)
        
        # With h=0: result = eps_hat - 1^5 * eps_init - sqrt(2) * 0 * sum(...) = eps_hat - eps_init
        expected = eps_hat - eps_init
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "zero_step_size_deterministic",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(result - expected))}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "zero_step_size_deterministic",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Zero noise input should give result = eps_hat - decay_factor * eps_init
    # When eps_noises = 0, the noise_sum term vanishes
    try:
        np.random.seed(43)
        B, D = 2, 3
        eps_hat = np.random.randn(B, D)
        eps_init = np.random.randn(B, D)
        eps_noises = np.zeros((5, B, D))
        eps_step_size = 0.1
        ld_steps = 5
        
        result = fn(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps)
        
        decay_factor = (1 - eps_step_size**2) ** ld_steps
        expected = eps_hat - decay_factor * eps_init
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "zero_noise_input",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(result - expected))}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "zero_noise_input",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Single Langevin step (ld_steps=1) should have predictable form
    # step_weights = [(1-h^2)^0] = [1], weighted_noises = h * eps_noises[0]
    # result = eps_hat - (1-h^2) * eps_init - sqrt(2) * h * eps_noises[0]
    try:
        np.random.seed(44)
        B, D = 2, 3
        eps_hat = np.random.randn(B, D)
        eps_init = np.random.randn(B, D)
        eps_noises = np.random.randn(1, B, D)
        eps_step_size = 0.1
        ld_steps = 1
        
        result = fn(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps)
        
        decay_factor = 1 - eps_step_size**2
        expected = eps_hat - decay_factor * eps_init - np.sqrt(2) * eps_step_size * eps_noises[0]
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "single_langevin_step",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(result - expected))}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "single_langevin_step",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Output shape must match (B, D1, ..., Dk)
    # Test with various tensor shapes
    try:
        np.random.seed(45)
        shapes = [(2, 3), (2, 3, 4), (1, 5, 2, 3)]
        all_passed = True
        
        for shape in shapes:
            eps_hat = np.random.randn(*shape)
            eps_init = np.random.randn(*shape)
            eps_noises = np.random.randn(3, *shape)
            eps_step_size = 0.1
            ld_steps = 3
            
            result = fn(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps)
            if result.shape != shape:
                all_passed = False
                break
        
        results.append({
            "name": "output_shape_preservation",
            "passed": all_passed,
            "detail": "OK" if all_passed else f"Shape mismatch for {shape}"
        })
    except Exception as e:
        results.append({
            "name": "output_shape_preservation",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Linearity in eps_hat
    # f(a*eps_hat1 + b*eps_hat2, eps_init, eps_noises, h, L) 
    #   = a*f(eps_hat1, ...) + b*f(eps_hat2, ...)
    # (holding eps_init and eps_noises fixed)
    try:
        np.random.seed(46)
        B, D = 2, 3
        eps_hat1 = np.random.randn(B, D)
        eps_hat2 = np.random.randn(B, D)
        eps_init = np.random.randn(B, D)
        eps_noises = np.random.randn(4, B, D)
        eps_step_size = 0.1
        ld_steps = 4
        
        a, b = 2.5, -1.3
        
        result1 = fn(eps_hat1, eps_init, eps_noises, eps_step_size, ld_steps)
        result2 = fn(eps_hat2, eps_init, eps_noises, eps_step_size, ld_steps)
        combined_result = fn(a*eps_hat1 + b*eps_hat2, eps_init, eps_noises, eps_step_size, ld_steps)
        
        expected = a*result1 + b*result2
        passed = np.allclose(combined_result, expected, atol=1e-6)
        results.append({
            "name": "linearity_in_eps_hat",
            "passed": passed,
            "detail": f"max diff: {np.max(np.abs(combined_result - expected))}" if not passed else "OK"
        })
    except Exception as e:
        results.append({
            "name": "linearity_in_eps_hat",
            "passed": False,
            "detail": str(e)
        })
    
    return results
