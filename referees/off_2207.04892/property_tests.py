import numpy as np

def check(fn):
    results = []
    
    # Test 1: Linearity in gradient ascent - output is linear combination of inputs
    # Property: mu_new = mu + gamma * grad_mu (exact mathematical property from spec)
    try:
        C = 5
        mu = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sigma = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        grad_mu = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        grad_sigma = np.array([0.05, 0.06, 0.07, 0.08, 0.09])
        gamma = 0.1
        
        mu_new, sigma_new = fn(mu, sigma, grad_mu, grad_sigma, gamma)
        
        # Check exact formula: mu_new = mu + gamma * grad_mu
        expected_mu = mu + gamma * grad_mu
        expected_sigma = sigma + gamma * grad_sigma
        
        mu_match = np.allclose(mu_new, expected_mu, atol=1e-6)
        sigma_match = np.allclose(sigma_new, expected_sigma, atol=1e-6)
        
        passed = mu_match and sigma_match
        detail = f"mu match: {mu_match}, sigma match: {sigma_match}"
        results.append({"name": "linearity_in_gradient_ascent", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "linearity_in_gradient_ascent", "passed": False, "detail": str(e)})
    
    # Test 2: Zero gradient produces identity operation
    # Property: If grad_mu = 0 and grad_sigma = 0, then output equals input
    try:
        C = 4
        mu = np.array([1.5, 2.5, 3.5, 4.5])
        sigma = np.array([0.1, 0.2, 0.3, 0.4])
        grad_mu = np.zeros(C)
        grad_sigma = np.zeros(C)
        gamma = 0.5
        
        mu_new, sigma_new = fn(mu, sigma, grad_mu, grad_sigma, gamma)
        
        mu_unchanged = np.allclose(mu_new, mu, atol=1e-6)
        sigma_unchanged = np.allclose(sigma_new, sigma, atol=1e-6)
        
        passed = mu_unchanged and sigma_unchanged
        detail = f"mu unchanged: {mu_unchanged}, sigma unchanged: {sigma_unchanged}"
        results.append({"name": "zero_gradient_identity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_gradient_identity", "passed": False, "detail": str(e)})
    
    # Test 3: Zero learning rate produces identity operation
    # Property: If gamma = 0, then output equals input regardless of gradients
    try:
        C = 3
        mu = np.array([0.5, 1.5, 2.5])
        sigma = np.array([0.2, 0.3, 0.4])
        grad_mu = np.array([10.0, 20.0, 30.0])
        grad_sigma = np.array([5.0, 10.0, 15.0])
        gamma = 0.0
        
        mu_new, sigma_new = fn(mu, sigma, grad_mu, grad_sigma, gamma)
        
        mu_unchanged = np.allclose(mu_new, mu, atol=1e-6)
        sigma_unchanged = np.allclose(sigma_new, sigma, atol=1e-6)
        
        passed = mu_unchanged and sigma_unchanged
        detail = f"mu unchanged: {mu_unchanged}, sigma unchanged: {sigma_unchanged}"
        results.append({"name": "zero_learning_rate_identity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_learning_rate_identity", "passed": False, "detail": str(e)})
    
    # Test 4: Output shape and type preservation
    # Property: Output shapes match input shapes [C], and are numpy arrays
    try:
        C = 6
        mu = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        sigma = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        grad_mu = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
        grad_sigma = np.array([0.001, 0.002, 0.003, 0.004, 0.005, 0.006])
        gamma = 0.5
        
        mu_new, sigma_new = fn(mu, sigma, grad_mu, grad_sigma, gamma)
        
        mu_shape_correct = mu_new.shape == (C,)
        sigma_shape_correct = sigma_new.shape == (C,)
        mu_is_ndarray = isinstance(mu_new, np.ndarray)
        sigma_is_ndarray = isinstance(sigma_new, np.ndarray)
        
        passed = mu_shape_correct and sigma_shape_correct and mu_is_ndarray and sigma_is_ndarray
        detail = f"mu shape: {mu_new.shape}, sigma shape: {sigma_new.shape}, types: {type(mu_new).__name__}, {type(sigma_new).__name__}"
        results.append({"name": "output_shape_and_type", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_and_type", "passed": False, "detail": str(e)})
    
    # Test 5: Superposition/additivity of updates
    # Property: Two sequential updates with gamma1, gamma2 equal one update with gamma1+gamma2
    try:
        C = 4
        mu = np.array([1.0, 2.0, 3.0, 4.0])
        sigma = np.array([0.5, 0.6, 0.7, 0.8])
        grad_mu = np.array([0.1, 0.2, 0.3, 0.4])
        grad_sigma = np.array([0.05, 0.06, 0.07, 0.08])
        gamma1 = 0.3
        gamma2 = 0.2
        
        # Sequential updates
        mu_temp, sigma_temp = fn(mu, sigma, grad_mu, grad_sigma, gamma1)
        mu_seq, sigma_seq = fn(mu_temp, sigma_temp, grad_mu, grad_sigma, gamma2)
        
        # Single update with combined gamma
        mu_single, sigma_single = fn(mu, sigma, grad_mu, grad_sigma, gamma1 + gamma2)
        
        mu_match = np.allclose(mu_seq, mu_single, atol=1e-6)
        sigma_match = np.allclose(sigma_seq, sigma_single, atol=1e-6)
        
        passed = mu_match and sigma_match
        detail = f"mu match: {mu_match}, sigma match: {sigma_match}"
        results.append({"name": "superposition_of_updates", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "superposition_of_updates", "passed": False, "detail": str(e)})
    
    return results
