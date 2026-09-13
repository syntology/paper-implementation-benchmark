import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero displacement property
    # If phi(s_{t+1}) = phi(s_t), then delta = 0, so reward should be 0 regardless of z
    try:
        np.random.seed(42)
        d = 5
        phi_s_t = np.random.randn(d)
        phi_s_t_plus_1 = phi_s_t.copy()  # Same state
        z = np.random.randn(d)
        
        reward = fn(phi_s_t, phi_s_t_plus_1, z)
        passed = np.abs(reward) < 1e-6
        detail = f"Zero displacement: reward={reward}, expected=0"
        results.append({"name": "zero_displacement", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_displacement", "passed": False, "detail": str(e)})
    
    # Test 2: Zero skill vector property
    # If z = 0, then reward = delta^T * 0 = 0 regardless of delta
    try:
        np.random.seed(43)
        d = 5
        phi_s_t = np.random.randn(d)
        phi_s_t_plus_1 = np.random.randn(d)
        z = np.zeros(d)
        
        reward = fn(phi_s_t, phi_s_t_plus_1, z)
        passed = np.abs(reward) < 1e-6
        detail = f"Zero skill: reward={reward}, expected=0"
        results.append({"name": "zero_skill", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_skill", "passed": False, "detail": str(e)})
    
    # Test 3: Linearity in displacement (translation invariance)
    # r(phi_s_t + c, phi_s_{t+1} + c, z) = r(phi_s_t, phi_s_{t+1}, z)
    # Because (phi_{t+1} + c) - (phi_t + c) = phi_{t+1} - phi_t
    try:
        np.random.seed(44)
        d = 5
        phi_s_t = np.random.randn(d)
        phi_s_t_plus_1 = np.random.randn(d)
        z = np.random.randn(d)
        c = np.random.randn(d) * 3.0
        
        reward_original = fn(phi_s_t, phi_s_t_plus_1, z)
        reward_translated = fn(phi_s_t + c, phi_s_t_plus_1 + c, z)
        
        passed = np.abs(reward_original - reward_translated) < 1e-6
        detail = f"Translation invariance: original={reward_original}, translated={reward_translated}, diff={np.abs(reward_original - reward_translated)}"
        results.append({"name": "translation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 4: Scaling property
    # r(phi_s_t, phi_s_{t+1}, alpha*z) = alpha * r(phi_s_t, phi_s_{t+1}, z)
    # Because delta^T * (alpha*z) = alpha * (delta^T * z)
    try:
        np.random.seed(45)
        d = 5
        phi_s_t = np.random.randn(d)
        phi_s_t_plus_1 = np.random.randn(d)
        z = np.random.randn(d)
        alpha = 2.5
        
        reward_original = fn(phi_s_t, phi_s_t_plus_1, z)
        reward_scaled = fn(phi_s_t, phi_s_t_plus_1, alpha * z)
        
        expected_scaled = alpha * reward_original
        passed = np.abs(reward_scaled - expected_scaled) < 1e-6
        detail = f"Skill scaling: scaled={reward_scaled}, expected={expected_scaled}, diff={np.abs(reward_scaled - expected_scaled)}"
        results.append({"name": "skill_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "skill_scaling", "passed": False, "detail": str(e)})
    
    # Test 5: Anti-symmetry property
    # r(phi_{t+1}, phi_t, z) = -r(phi_t, phi_{t+1}, z)
    # Because (phi_t - phi_{t+1})^T * z = -(phi_{t+1} - phi_t)^T * z
    try:
        np.random.seed(46)
        d = 5
        phi_s_t = np.random.randn(d)
        phi_s_t_plus_1 = np.random.randn(d)
        z = np.random.randn(d)
        
        reward_forward = fn(phi_s_t, phi_s_t_plus_1, z)
        reward_backward = fn(phi_s_t_plus_1, phi_s_t, z)
        
        passed = np.abs(reward_forward + reward_backward) < 1e-6
        detail = f"Anti-symmetry: forward={reward_forward}, backward={reward_backward}, sum={reward_forward + reward_backward}"
        results.append({"name": "anti_symmetry", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "anti_symmetry", "passed": False, "detail": str(e)})
    
    return results
