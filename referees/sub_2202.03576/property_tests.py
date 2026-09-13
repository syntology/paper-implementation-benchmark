import numpy as np

def check(fn):
    results = []
    
    # Test 1: Clipping bounds are enforced
    try:
        np.random.seed(42)
        d = 5
        C = 3
        epsilon = 0.4
        
        x_prime = np.random.randn(d)
        # Create W and B that exceed the clipping bounds
        W = np.random.uniform(-2, 3, (C, d))
        B = np.random.uniform(-2, 2, (C, d))
        
        result = fn(x_prime, W, B, epsilon)
        
        # Check output shape
        shape_correct = result.shape == (C, d)
        
        # Compute expected bounds based on clipped parameters
        W_clipped = np.clip(W, 1 - epsilon/2, 1 + epsilon/2)
        B_clipped = np.clip(B, -epsilon/2, epsilon/2)
        
        # For each class, result should be W_clipped[c] * x_prime + B_clipped[c]
        # The bounds depend on x_prime values
        expected = W_clipped * x_prime[np.newaxis, :] + B_clipped
        
        bounds_satisfied = np.allclose(result, expected, atol=1e-6)
        
        passed = shape_correct and bounds_satisfied
        detail = "Output shape and clipping bounds verified" if passed else f"Shape: {shape_correct}, Bounds: {bounds_satisfied}"
        results.append({"name": "clipping_bounds_enforced", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "clipping_bounds_enforced", "passed": False, "detail": str(e)})
    
    # Test 2: Zero perturbation (epsilon=0) forces identity-like transformation
    try:
        np.random.seed(43)
        d = 4
        C = 2
        epsilon = 0.0
        
        x_prime = np.random.randn(d)
        W = np.random.uniform(0.5, 1.5, (C, d))
        B = np.random.uniform(-1, 1, (C, d))
        
        result = fn(x_prime, W, B, epsilon)
        
        # With epsilon=0: W clips to [1, 1] = 1, B clips to [0, 0] = 0
        # So result should be 1 * x_prime + 0 = x_prime for all classes
        expected = np.tile(x_prime, (C, 1))
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = "Zero epsilon produces identity transformation" if passed else f"Max diff: {np.max(np.abs(result - expected))}"
        results.append({"name": "zero_epsilon_identity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_epsilon_identity", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling invariance - if x_prime is scaled, output scales proportionally
    try:
        np.random.seed(44)
        d = 6
        C = 3
        epsilon = 0.6
        
        x_prime = np.random.randn(d) + 1.0  # Avoid zeros
        W = np.random.uniform(0.5, 1.5, (C, d))
        B = np.random.uniform(-0.5, 0.5, (C, d))
        
        result1 = fn(x_prime, W, B, epsilon)
        
        scale = 2.0
        x_prime_scaled = scale * x_prime
        result2 = fn(x_prime_scaled, W, B, epsilon)
        
        # W and B clip the same way in both cases
        # result1[c] = W_clip[c] * x_prime + B_clip[c]
        # result2[c] = W_clip[c] * (scale * x_prime) + B_clip[c]
        #            = scale * W_clip[c] * x_prime + B_clip[c]
        # So: result2 = scale * (result1 - B_clip) + B_clip
        #            = scale * result1 - scale * B_clip + B_clip
        #            = scale * result1 + (1 - scale) * B_clip
        
        W_clipped = np.clip(W, 1 - epsilon/2, 1 + epsilon/2)
        B_clipped = np.clip(B, -epsilon/2, epsilon/2)
        expected = scale * result1 + (1 - scale) * B_clipped
        
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = "Input scaling property verified" if passed else f"Max diff: {np.max(np.abs(result2 - expected))}"
        results.append({"name": "input_scaling_property", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "input_scaling_property", "passed": False, "detail": str(e)})
    
    # Test 4: W and B within bounds are unchanged
    try:
        np.random.seed(45)
        d = 5
        C = 2
        epsilon = 1.0
        
        x_prime = np.random.randn(d)
        # Create W and B already within clipping bounds
        W = np.random.uniform(1 - epsilon/2 + 0.01, 1 + epsilon/2 - 0.01, (C, d))
        B = np.random.uniform(-epsilon/2 + 0.01, epsilon/2 - 0.01, (C, d))
        
        result = fn(x_prime, W, B, epsilon)
        
        # Since W and B are within bounds, they should not be clipped
        expected = W * x_prime[np.newaxis, :] + B
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = "Parameters within bounds unchanged" if passed else f"Max diff: {np.max(np.abs(result - expected))}"
        results.append({"name": "no_clipping_when_within_bounds", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "no_clipping_when_within_bounds", "passed": False, "detail": str(e)})
    
    # Test 5: Translation property - adding constant to x_prime
    try:
        np.random.seed(46)
        d = 4
        C = 3
        epsilon = 0.8
        
        x_prime = np.random.randn(d)
        W = np.random.uniform(0.8, 1.3, (C, d))
        B = np.random.uniform(-0.6, 0.6, (C, d))
        
        result1 = fn(x_prime, W, B, epsilon)
        
        translation = 3.0
        x_prime_translated = x_prime + translation
        result2 = fn(x_prime_translated, W, B, epsilon)
        
        # W and B clip the same way
        # result1[c] = W_clip[c] * x_prime + B_clip[c]
        # result2[c] = W_clip[c] * (x_prime + translation) + B_clip[c]
        #            = W_clip[c] * x_prime + W_clip[c] * translation + B_clip[c]
        #            = result1[c] + W_clip[c] * translation
        
        W_clipped = np.clip(W, 1 - epsilon/2, 1 + epsilon/2)
        expected = result1 + W_clipped * translation
        
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = "Input translation property verified" if passed else f"Max diff: {np.max(np.abs(result2 - expected))}"
        results.append({"name": "input_translation_property", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "input_translation_property", "passed": False, "detail": str(e)})
    
    return results
