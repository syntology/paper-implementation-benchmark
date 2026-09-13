import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity
    # The loss is a sum of squared terms divided by positive sigma values,
    # so it must always be non-negative.
    try:
        np.random.seed(42)
        D = 10
        epsilon = np.random.randn(D)
        epsilon_theta = np.random.randn(D)
        sigma = np.abs(np.random.randn(D)) + 0.1  # ensure positive
        
        loss = fn(epsilon, epsilon_theta, sigma)
        passed = loss >= -1e-6  # allow tiny numerical error
        detail = f"loss={loss}, expected >= 0"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Zero loss when predictions match noise
    # When epsilon == epsilon_theta, all numerators are 0, so loss must be 0.
    try:
        np.random.seed(43)
        D = 8
        epsilon = np.random.randn(D)
        epsilon_theta = epsilon.copy()
        sigma = np.abs(np.random.randn(D)) + 0.1
        
        loss = fn(epsilon, epsilon_theta, sigma)
        passed = np.abs(loss) < 1e-6
        detail = f"loss={loss}, expected ~0"
        results.append({"name": "zero_loss_perfect_prediction", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_loss_perfect_prediction", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling sigma scales the loss inversely
    # If sigma is scaled by factor c > 0, the loss should scale by 1/c.
    # loss(sigma) = sum((eps[i] - eps_theta[i])^2 / sigma[i])
    # loss(c*sigma) = sum((eps[i] - eps_theta[i])^2 / (c*sigma[i])) = loss(sigma) / c
    try:
        np.random.seed(44)
        D = 6
        epsilon = np.random.randn(D)
        epsilon_theta = np.random.randn(D)
        sigma = np.abs(np.random.randn(D)) + 0.1
        
        loss1 = fn(epsilon, epsilon_theta, sigma)
        scale_factor = 2.5
        loss2 = fn(epsilon, epsilon_theta, scale_factor * sigma)
        
        expected_ratio = 1.0 / scale_factor
        actual_ratio = loss2 / (loss1 + 1e-10)  # avoid division by zero
        passed = np.abs(actual_ratio - expected_ratio) < 1e-6
        detail = f"loss1={loss1}, loss2={loss2}, ratio={actual_ratio}, expected={expected_ratio}"
        results.append({"name": "sigma_scaling_inverse", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "sigma_scaling_inverse", "passed": False, "detail": str(e)})
    
    # Test 4: Additive shift in both epsilon and epsilon_theta cancels out
    # loss(epsilon + c, epsilon_theta + c, sigma) = loss(epsilon, epsilon_theta, sigma)
    # because the difference (epsilon - epsilon_theta) is invariant to constant shifts.
    try:
        np.random.seed(45)
        D = 7
        epsilon = np.random.randn(D)
        epsilon_theta = np.random.randn(D)
        sigma = np.abs(np.random.randn(D)) + 0.1
        
        loss1 = fn(epsilon, epsilon_theta, sigma)
        shift = np.array([3.14] * D)
        loss2 = fn(epsilon + shift, epsilon_theta + shift, sigma)
        
        passed = np.abs(loss1 - loss2) < 1e-6
        detail = f"loss1={loss1}, loss2={loss2}, diff={np.abs(loss1 - loss2)}"
        results.append({"name": "translation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Closed-form verification on simple case
    # D=2, epsilon=[1, 2], epsilon_theta=[0, 1], sigma=[1, 2]
    # loss = (1-0)^2/1 + (2-1)^2/2 = 1 + 0.5 = 1.5
    try:
        epsilon = np.array([1.0, 2.0])
        epsilon_theta = np.array([0.0, 1.0])
        sigma = np.array([1.0, 2.0])
        
        loss = fn(epsilon, epsilon_theta, sigma)
        expected = 1.5
        passed = np.abs(loss - expected) < 1e-6
        detail = f"loss={loss}, expected={expected}"
        results.append({"name": "closed_form_simple", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "closed_form_simple", "passed": False, "detail": str(e)})
    
    return results
