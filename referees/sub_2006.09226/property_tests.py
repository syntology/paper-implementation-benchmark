import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero TD error when q_values equals TD target
    # Mathematical property: MSE should be 0 when predictions match targets exactly
    try:
        batch_size = 5
        rewards = np.array([1.0, 2.0, 3.0, 0.5, 1.5])
        next_q_values = np.array([2.0, 3.0, 1.0, 2.5, 0.5])
        gamma = 0.99
        
        # Construct q_values to exactly match TD targets
        td_targets = rewards + gamma * next_q_values
        q_values = td_targets.copy()
        
        loss = fn(q_values, rewards, next_q_values, gamma)
        
        passed = np.abs(loss) < 1e-6
        results.append({
            "name": "Zero loss when predictions match targets",
            "passed": passed,
            "detail": f"Expected loss ≈ 0, got {loss}"
        })
    except Exception as e:
        results.append({
            "name": "Zero loss when predictions match targets",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Non-negativity of MSE loss
    # Mathematical property: MSE is always non-negative
    try:
        np.random.seed(42)
        batch_size = 10
        q_values = np.random.randn(batch_size)
        rewards = np.random.randn(batch_size)
        next_q_values = np.random.randn(batch_size)
        gamma = 0.99
        
        loss = fn(q_values, rewards, next_q_values, gamma)
        
        passed = loss >= -1e-6  # Allow tiny numerical error
        results.append({
            "name": "MSE loss is non-negative",
            "passed": passed,
            "detail": f"Expected loss >= 0, got {loss}"
        })
    except Exception as e:
        results.append({
            "name": "MSE loss is non-negative",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Scaling invariance of loss under uniform scaling
    # Mathematical property: If all q_values and next_q_values scale by c, 
    # and rewards scale by c, loss scales by c^2
    try:
        np.random.seed(43)
        batch_size = 8
        q_values = np.random.randn(batch_size)
        rewards = np.random.randn(batch_size)
        next_q_values = np.random.randn(batch_size)
        gamma = 0.95
        
        loss1 = fn(q_values, rewards, next_q_values, gamma)
        
        # Scale all inputs by constant c
        c = 2.5
        loss2 = fn(c * q_values, c * rewards, c * next_q_values, gamma)
        
        expected_loss2 = c * c * loss1
        passed = np.abs(loss2 - expected_loss2) < 1e-5 * (np.abs(expected_loss2) + 1)
        results.append({
            "name": "Scaling invariance: loss scales by c^2",
            "passed": passed,
            "detail": f"Expected {expected_loss2}, got {loss2}"
        })
    except Exception as e:
        results.append({
            "name": "Scaling invariance: loss scales by c^2",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Gamma = 0 reduces to immediate reward prediction error
    # Mathematical property: When gamma=0, TD target = rewards only,
    # so loss = mean((q_values - rewards)^2)
    try:
        batch_size = 6
        q_values = np.array([1.0, 2.0, 3.0, 0.5, 1.5, 2.5])
        rewards = np.array([0.9, 2.1, 2.9, 0.6, 1.4, 2.6])
        next_q_values = np.array([10.0, 20.0, 30.0, 5.0, 15.0, 25.0])  # Should be ignored
        gamma = 0.0
        
        loss = fn(q_values, rewards, next_q_values, gamma)
        
        # Expected: mean squared error between q_values and rewards
        expected_loss = np.mean((q_values - rewards) ** 2)
        
        passed = np.abs(loss - expected_loss) < 1e-6
        results.append({
            "name": "Gamma=0 case: loss = MSE(q_values, rewards)",
            "passed": passed,
            "detail": f"Expected {expected_loss}, got {loss}"
        })
    except Exception as e:
        results.append({
            "name": "Gamma=0 case: loss = MSE(q_values, rewards)",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Single element batch
    # Mathematical property: For batch_size=1, loss = (q - (r + gamma*q'))^2
    try:
        q_values = np.array([5.0])
        rewards = np.array([1.0])
        next_q_values = np.array([2.0])
        gamma = 0.9
        
        loss = fn(q_values, rewards, next_q_values, gamma)
        
        td_target = rewards[0] + gamma * next_q_values[0]
        td_error = q_values[0] - td_target
        expected_loss = td_error ** 2
        
        passed = np.abs(loss - expected_loss) < 1e-6
        results.append({
            "name": "Single element batch computes correct MSE",
            "passed": passed,
            "detail": f"Expected {expected_loss}, got {loss}"
        })
    except Exception as e:
        results.append({
            "name": "Single element batch computes correct MSE",
            "passed": False,
            "detail": str(e)
        })
    
    return results
