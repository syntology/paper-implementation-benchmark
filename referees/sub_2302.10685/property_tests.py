import numpy as np

def check(fn):
    results = []
    
    # Test 1: Return value is always >= theta
    # Property: shift = max(theta, theta + epsilon - max_v) >= theta by definition
    try:
        theta = 5.0
        epsilon = 2.0
        membrane_potentials = np.array([1.0, 3.0, 7.0, 2.0])
        spikes = np.array([0, 1, 0, 1])
        
        shift = fn(membrane_potentials, spikes, theta, epsilon)
        
        passed = shift >= theta - 1e-6
        detail = f"shift={shift}, theta={theta}, shift >= theta: {passed}"
        results.append({"name": "shift_lower_bound_theta", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "shift_lower_bound_theta", "passed": False, "detail": str(e)})
    
    # Test 2: When all spikes are 1 (no zeros), return theta
    # Property: If no spike==0, max_v is undefined, so return theta (first arg of max)
    try:
        theta = 3.5
        epsilon = 1.0
        membrane_potentials = np.array([5.0, 6.0, 7.0])
        spikes = np.array([1, 1, 1])
        
        shift = fn(membrane_potentials, spikes, theta, epsilon)
        
        passed = abs(shift - theta) < 1e-6
        detail = f"shift={shift}, theta={theta}, all_spikes_1: {passed}"
        results.append({"name": "all_spikes_one_returns_theta", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "all_spikes_one_returns_theta", "passed": False, "detail": str(e)})
    
    # Test 3: When theta + epsilon - max_v < theta, return theta
    # Property: shift = max(theta, theta + epsilon - max_v); if epsilon < max_v, first arg wins
    try:
        theta = 10.0
        epsilon = 2.0
        membrane_potentials = np.array([1.0, 5.0, 8.0, 3.0])
        spikes = np.array([0, 1, 0, 1])
        # max_v among spike==0 is max(1.0, 8.0) = 8.0
        # theta + epsilon - max_v = 10.0 + 2.0 - 8.0 = 4.0 < 10.0
        # so shift should be 10.0
        
        shift = fn(membrane_potentials, spikes, theta, epsilon)
        
        passed = abs(shift - theta) < 1e-6
        detail = f"shift={shift}, theta={theta}, epsilon_small_case: {passed}"
        results.append({"name": "epsilon_small_returns_theta", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "epsilon_small_returns_theta", "passed": False, "detail": str(e)})
    
    # Test 4: When theta + epsilon - max_v > theta, return theta + epsilon - max_v
    # Property: shift = max(theta, theta + epsilon - max_v); if epsilon > max_v, second arg wins
    try:
        theta = 5.0
        epsilon = 10.0
        membrane_potentials = np.array([1.0, 2.0, 3.0, 4.0])
        spikes = np.array([0, 1, 0, 1])
        # max_v among spike==0 is max(1.0, 3.0) = 3.0
        # theta + epsilon - max_v = 5.0 + 10.0 - 3.0 = 12.0 > 5.0
        # so shift should be 12.0
        
        shift = fn(membrane_potentials, spikes, theta, epsilon)
        expected = theta + epsilon - 3.0
        
        passed = abs(shift - expected) < 1e-6
        detail = f"shift={shift}, expected={expected}, epsilon_large_case: {passed}"
        results.append({"name": "epsilon_large_returns_formula", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "epsilon_large_returns_formula", "passed": False, "detail": str(e)})
    
    # Test 5: Single element with spike=0
    # Property: max_v is that single element, shift = max(theta, theta + epsilon - element)
    try:
        theta = 2.0
        epsilon = 3.0
        membrane_potentials = np.array([1.5])
        spikes = np.array([0])
        # max_v = 1.5
        # theta + epsilon - max_v = 2.0 + 3.0 - 1.5 = 3.5
        # shift = max(2.0, 3.5) = 3.5
        
        shift = fn(membrane_potentials, spikes, theta, epsilon)
        expected = 3.5
        
        passed = abs(shift - expected) < 1e-6
        detail = f"shift={shift}, expected={expected}, single_element: {passed}"
        results.append({"name": "single_element_spike_zero", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "single_element_spike_zero", "passed": False, "detail": str(e)})
    
    return results
