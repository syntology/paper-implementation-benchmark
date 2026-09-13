import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape matches input state shape
    try:
        state_dim = 5
        s_t = np.random.RandomState(42).randn(state_dim)
        a_t = np.random.RandomState(43).randn(3)
        delta_pred = np.random.RandomState(44).randn(state_dim)
        
        result = fn(s_t, a_t, delta_pred)
        
        passed = result.shape == (state_dim,) and result.ndim == 1
        detail = f"Expected shape ({state_dim},), got {result.shape}" if not passed else "Shape correct"
        results.append({"name": "output_shape_matches_state_dim", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_matches_state_dim", "passed": False, "detail": str(e)})
    
    # Test 2: Element-wise addition property: s_{t+1} = s_t + delta_pred
    try:
        state_dim = 4
        s_t = np.array([1.0, 2.0, 3.0, 4.0])
        a_t = np.array([0.5, -0.5])
        delta_pred = np.array([0.1, -0.2, 0.3, -0.4])
        
        result = fn(s_t, a_t, delta_pred)
        expected = s_t + delta_pred
        
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"Expected {expected}, got {result}" if not passed else "Element-wise addition correct"
        results.append({"name": "element_wise_addition", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "element_wise_addition", "passed": False, "detail": str(e)})
    
    # Test 3: Zero delta produces identity: s_{t+1} = s_t when delta_pred = 0
    try:
        state_dim = 6
        s_t = np.array([1.5, -2.3, 0.0, 4.1, -0.5, 3.2])
        a_t = np.array([1.0, 2.0, 3.0])
        delta_pred = np.zeros(state_dim)
        
        result = fn(s_t, a_t, delta_pred)
        
        passed = np.allclose(result, s_t, atol=1e-6)
        detail = f"Expected {s_t}, got {result}" if not passed else "Identity property holds"
        results.append({"name": "zero_delta_identity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_delta_identity", "passed": False, "detail": str(e)})
    
    # Test 4: Linearity in delta: scaling delta scales the output change
    try:
        state_dim = 3
        s_t = np.array([1.0, 2.0, 3.0])
        a_t = np.array([0.5])
        delta_pred = np.array([0.2, -0.4, 0.6])
        scale = 2.5
        
        result1 = fn(s_t, a_t, delta_pred)
        result2 = fn(s_t, a_t, scale * delta_pred)
        
        # s_{t+1}^{(2)} - s_t should equal scale * (s_{t+1}^{(1)} - s_t)
        change1 = result1 - s_t
        change2 = result2 - s_t
        expected_change2 = scale * change1
        
        passed = np.allclose(change2, expected_change2, atol=1e-6)
        detail = f"Expected change {expected_change2}, got {change2}" if not passed else "Linearity in delta holds"
        results.append({"name": "linearity_in_delta", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "linearity_in_delta", "passed": False, "detail": str(e)})
    
    # Test 5: Translation invariance in state: shifting s_t shifts output by same amount
    try:
        state_dim = 4
        s_t = np.array([1.0, 2.0, 3.0, 4.0])
        a_t = np.array([0.1, 0.2])
        delta_pred = np.array([0.05, -0.1, 0.15, -0.2])
        translation = np.array([10.0, -5.0, 3.0, 2.0])
        
        result1 = fn(s_t, a_t, delta_pred)
        result2 = fn(s_t + translation, a_t, delta_pred)
        
        # Output should shift by same translation
        passed = np.allclose(result2, result1 + translation, atol=1e-6)
        detail = f"Expected {result1 + translation}, got {result2}" if not passed else "Translation invariance holds"
        results.append({"name": "translation_invariance_state", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "translation_invariance_state", "passed": False, "detail": str(e)})
    
    return results
