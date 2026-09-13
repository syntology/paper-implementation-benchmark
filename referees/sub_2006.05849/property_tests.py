import numpy as np

def check(fn):
    results = []
    
    # Test 1: Perfect predictions should yield zero loss
    # When y_pred matches y_target exactly (after clipping), loss should be near zero
    try:
        y_target = np.array([0.0, 1.0, 0.0, 1.0])
        y_pred = np.array([1e-7, 1.0 - 1e-7, 1e-7, 1.0 - 1e-7])
        loss = fn(y_pred, y_target)
        # log(eps) ≈ -16.12, log(1-eps) ≈ -16.12, so loss should be very small
        passed = loss < 1e-5
        results.append({
            "name": "perfect_predictions_near_zero_loss",
            "passed": passed,
            "detail": f"Loss for perfect predictions: {loss}, expected < 1e-5"
        })
    except Exception as e:
        results.append({
            "name": "perfect_predictions_near_zero_loss",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Loss is non-negative
    # BCE loss is always >= 0 by mathematical definition
    try:
        np.random.seed(42)
        y_target = np.random.randint(0, 2, size=20).astype(float)
        y_pred = np.random.uniform(0.1, 0.9, size=20)
        loss = fn(y_pred, y_target)
        passed = loss >= 0.0
        results.append({
            "name": "loss_non_negative",
            "passed": passed,
            "detail": f"Loss value: {loss}, expected >= 0"
        })
    except Exception as e:
        results.append({
            "name": "loss_non_negative",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Worst case predictions yield high loss
    # When y_pred is opposite to y_target (clipped), loss should be large
    try:
        y_target = np.array([0.0, 1.0, 0.0, 1.0])
        # Opposite predictions (clipped to valid range)
        y_pred = np.array([1.0 - 1e-7, 1e-7, 1.0 - 1e-7, 1e-7])
        loss = fn(y_pred, y_target)
        # log(eps) ≈ -16.12, so loss should be large
        passed = loss > 10.0
        results.append({
            "name": "worst_case_high_loss",
            "passed": passed,
            "detail": f"Loss for opposite predictions: {loss}, expected > 10.0"
        })
    except Exception as e:
        results.append({
            "name": "worst_case_high_loss",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Permutation invariance
    # Reordering samples should not change the mean loss
    try:
        np.random.seed(42)
        y_target = np.random.randint(0, 2, size=10).astype(float)
        y_pred = np.random.uniform(0.1, 0.9, size=10)
        
        loss1 = fn(y_pred, y_target)
        
        # Permute both arrays identically
        perm = np.array([3, 1, 4, 0, 2, 5, 7, 6, 9, 8])
        y_pred_perm = y_pred[perm]
        y_target_perm = y_target[perm]
        loss2 = fn(y_pred_perm, y_target_perm)
        
        passed = np.abs(loss1 - loss2) < 1e-6
        results.append({
            "name": "permutation_invariance",
            "passed": passed,
            "detail": f"Loss before permutation: {loss1}, after: {loss2}, diff: {np.abs(loss1 - loss2)}"
        })
    except Exception as e:
        results.append({
            "name": "permutation_invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Uniform predictions with uniform targets
    # When all predictions are 0.5 and all targets are 0.5 (or mixed uniformly),
    # loss should be log(2) ≈ 0.693 (symmetric case)
    try:
        y_target = np.array([0.0, 1.0, 0.0, 1.0])
        y_pred = np.array([0.5, 0.5, 0.5, 0.5])
        loss = fn(y_pred, y_target)
        expected = np.log(2.0)  # -[0.5*log(0.5) + 0.5*log(0.5)] = log(2)
        passed = np.abs(loss - expected) < 1e-6
        results.append({
            "name": "uniform_predictions_symmetric_loss",
            "passed": passed,
            "detail": f"Loss: {loss}, expected: {expected}, diff: {np.abs(loss - expected)}"
        })
    except Exception as e:
        results.append({
            "name": "uniform_predictions_symmetric_loss",
            "passed": False,
            "detail": str(e)
        })
    
    return results
