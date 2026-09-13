import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity of loss
    # MSE loss is always non-negative by definition
    def test_non_negative():
        try:
            q_current = np.array([1.0, 2.0, 3.0])
            reward = np.array([0.5, 1.0, 1.5])
            gamma_v = 0.99
            v_mve_next = np.array([2.0, 3.0, 4.0])
            
            loss = fn(q_current, reward, gamma_v, v_mve_next)
            
            passed = loss >= 0.0
            detail = f"Loss = {loss}, expected >= 0" if not passed else "Non-negative as expected"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "non_negative_loss", "passed": test_non_negative()[0], "detail": test_non_negative()[1]})
    
    # Test 2: Zero loss when q_current equals target
    # When q_current = reward + gamma_v * v_mve_next, loss should be exactly 0
    def test_zero_loss_at_target():
        try:
            reward = np.array([1.0, 2.0, 3.0])
            gamma_v = 0.99
            v_mve_next = np.array([10.0, 20.0, 30.0])
            
            # Set q_current to the target value
            q_current = reward + gamma_v * v_mve_next
            
            loss = fn(q_current, reward, gamma_v, v_mve_next)
            
            passed = np.abs(loss) < 1e-6
            detail = f"Loss = {loss}, expected ~0" if not passed else "Zero loss at target as expected"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "zero_loss_at_target", "passed": test_zero_loss_at_target()[0], "detail": test_zero_loss_at_target()[1]})
    
    # Test 3: Scaling invariance of loss with respect to reward and v_mve_next
    # If both reward and v_mve_next are scaled by constant c, and q_current is scaled by c,
    # the loss should scale by c^2 (since MSE scales quadratically)
    def test_scaling_invariance():
        try:
            q_current = np.array([1.0, 2.0])
            reward = np.array([0.5, 1.0])
            gamma_v = 0.99
            v_mve_next = np.array([2.0, 3.0])
            
            loss1 = fn(q_current, reward, gamma_v, v_mve_next)
            
            # Scale all by factor 2
            scale = 2.0
            q_current_scaled = q_current * scale
            reward_scaled = reward * scale
            v_mve_next_scaled = v_mve_next * scale
            
            loss2 = fn(q_current_scaled, reward_scaled, gamma_v, v_mve_next_scaled)
            
            # Loss should scale by scale^2
            expected_loss2 = loss1 * (scale ** 2)
            passed = np.abs(loss2 - expected_loss2) < 1e-5
            detail = f"Loss1={loss1}, Loss2={loss2}, Expected={expected_loss2}" if not passed else "Scaling invariance verified"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "scaling_invariance", "passed": test_scaling_invariance()[0], "detail": test_scaling_invariance()[1]})
    
    # Test 4: Gamma=0 case (no discounting)
    # When gamma_v=0, target becomes just reward, loss = 0.5 * mean((q_current - reward)^2)
    def test_gamma_zero():
        try:
            q_current = np.array([1.0, 2.0, 3.0])
            reward = np.array([1.5, 2.5, 3.5])
            gamma_v = 0.0
            v_mve_next = np.array([100.0, 200.0, 300.0])  # Should be ignored
            
            loss = fn(q_current, reward, gamma_v, v_mve_next)
            
            # Expected: 0.5 * mean((q_current - reward)^2)
            expected_loss = 0.5 * np.mean((q_current - reward) ** 2)
            
            passed = np.abs(loss - expected_loss) < 1e-6
            detail = f"Loss={loss}, Expected={expected_loss}" if not passed else "Gamma=0 case correct"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "gamma_zero_case", "passed": test_gamma_zero()[0], "detail": test_gamma_zero()[1]})
    
    # Test 5: Scalar vs array consistency
    # Single sample as scalar should match single-element array
    def test_scalar_array_consistency():
        try:
            q_current_scalar = 1.5
            reward_scalar = 0.5
            gamma_v = 0.99
            v_mve_next_scalar = 2.0
            
            loss_scalar = fn(q_current_scalar, reward_scalar, gamma_v, v_mve_next_scalar)
            
            q_current_array = np.array([1.5])
            reward_array = np.array([0.5])
            v_mve_next_array = np.array([2.0])
            
            loss_array = fn(q_current_array, reward_array, gamma_v, v_mve_next_array)
            
            passed = np.abs(loss_scalar - loss_array) < 1e-6
            detail = f"Scalar loss={loss_scalar}, Array loss={loss_array}" if not passed else "Scalar/array consistency verified"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "scalar_array_consistency", "passed": test_scalar_array_consistency()[0], "detail": test_scalar_array_consistency()[1]})
    
    return results
