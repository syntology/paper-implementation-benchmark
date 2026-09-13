import numpy as np

def check(fn):
    results = []
    
    # Test 1: Zero incentives should reduce to standard policy gradient
    # Property: When incentives are all zero, the update should depend only on rewards
    try:
        T = 5
        np.random.seed(42)
        log_probs = np.random.randn(T)
        rewards = np.random.randn(T)
        incentives_zero = np.zeros(T)
        incentives_nonzero = np.random.randn(T)
        baseline = 0.5
        learning_rate = 0.01
        
        update_with_zero_incentives = fn(log_probs, rewards, incentives_zero, baseline, learning_rate)
        update_with_nonzero_incentives = fn(log_probs, rewards, incentives_nonzero, baseline, learning_rate)
        
        # These should differ (with high probability for random incentives)
        # and the zero case should be deterministic based only on rewards
        update_with_zero_incentives_2 = fn(log_probs, rewards, incentives_zero, baseline, learning_rate)
        
        passed = np.isclose(update_with_zero_incentives, update_with_zero_incentives_2, atol=1e-6)
        detail = f"Zero incentives reproducibility: {update_with_zero_incentives} vs {update_with_zero_incentives_2}"
        results.append({"name": "zero_incentives_reproducible", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_incentives_reproducible", "passed": False, "detail": str(e)})
    
    # Test 2: Scaling learning rate should scale output linearly
    # Property: delta_theta(lr) = lr * delta_theta(1.0) for any lr
    try:
        T = 4
        np.random.seed(43)
        log_probs = np.random.randn(T)
        rewards = np.random.randn(T)
        incentives = np.random.randn(T)
        baseline = 0.3
        
        update_lr_1 = fn(log_probs, rewards, incentives, baseline, 1.0)
        update_lr_2 = fn(log_probs, rewards, incentives, baseline, 2.0)
        update_lr_half = fn(log_probs, rewards, incentives, baseline, 0.5)
        
        # Check linear scaling
        passed = (np.isclose(update_lr_2, 2.0 * update_lr_1, atol=1e-6) and 
                  np.isclose(update_lr_half, 0.5 * update_lr_1, atol=1e-6))
        detail = f"lr=1.0: {update_lr_1}, lr=2.0: {update_lr_2} (expect {2*update_lr_1}), lr=0.5: {update_lr_half} (expect {0.5*update_lr_1})"
        results.append({"name": "learning_rate_linear_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "learning_rate_linear_scaling", "passed": False, "detail": str(e)})
    
    # Test 3: Baseline translation invariance
    # Property: Changing baseline by constant c should change output by learning_rate * sum(log_probs) * c
    # (because advantages shift uniformly, affecting the gradient sum)
    try:
        T = 3
        np.random.seed(44)
        log_probs = np.random.randn(T)
        rewards = np.random.randn(T)
        incentives = np.random.randn(T)
        baseline_1 = 0.0
        baseline_2 = 1.5
        learning_rate = 0.01
        
        update_1 = fn(log_probs, rewards, incentives, baseline_1, learning_rate)
        update_2 = fn(log_probs, rewards, incentives, baseline_2, learning_rate)
        
        # Difference should be -learning_rate * sum(log_probs) * (baseline_2 - baseline_1)
        expected_diff = -learning_rate * np.sum(log_probs) * (baseline_2 - baseline_1)
        actual_diff = update_2 - update_1
        
        passed = np.isclose(actual_diff, expected_diff, atol=1e-6)
        detail = f"Expected diff: {expected_diff}, actual diff: {actual_diff}"
        results.append({"name": "baseline_translation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "baseline_translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 4: Single timestep degenerate case
    # Property: With T=1, delta_theta = learning_rate * log_prob[0] * (reward[0] + incentive[0] - baseline)
    try:
        T = 1
        log_prob = np.array([2.0])
        reward = np.array([3.0])
        incentive = np.array([1.0])
        baseline = 0.5
        learning_rate = 0.1
        
        update = fn(log_prob, reward, incentive, baseline, learning_rate)
        
        # Manual computation: return[0] = 3.0 + 1.0 = 4.0
        # advantage[0] = 4.0 - 0.5 = 3.5
        # grad = 2.0 * 3.5 = 7.0
        # delta_theta = 0.1 * 7.0 = 0.7
        expected = learning_rate * log_prob[0] * (reward[0] + incentive[0] - baseline)
        
        passed = np.isclose(update, expected, atol=1e-6)
        detail = f"Expected: {expected}, got: {update}"
        results.append({"name": "single_timestep_closed_form", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "single_timestep_closed_form", "passed": False, "detail": str(e)})
    
    # Test 5: All-zero rewards and incentives with nonzero baseline
    # Property: With all rewards and incentives zero, advantages are all -baseline,
    # so delta_theta = -learning_rate * baseline * sum(log_probs)
    try:
        T = 4
        np.random.seed(45)
        log_probs = np.random.randn(T)
        rewards = np.zeros(T)
        incentives = np.zeros(T)
        baseline = 2.0
        learning_rate = 0.05
        
        update = fn(log_probs, rewards, incentives, baseline, learning_rate)
        
        # All advantages = 0 - 2.0 = -2.0
        # grad = sum(log_probs[t] * (-2.0)) = -2.0 * sum(log_probs)
        # delta_theta = 0.05 * (-2.0 * sum(log_probs))
        expected = -learning_rate * baseline * np.sum(log_probs)
        
        passed = np.isclose(update, expected, atol=1e-6)
        detail = f"Expected: {expected}, got: {update}"
        results.append({"name": "zero_rewards_incentives_closed_form", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_rewards_incentives_closed_form", "passed": False, "detail": str(e)})
    
    return results
