import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity
    # MSE loss must always be >= 0 (sum of squares)
    try:
        y_pred = np.array([1.0, 2.0, 3.0])
        y_true = np.array([1.5, 2.5, 3.5])
        loss = fn(y_pred, y_true)
        passed = loss >= 0.0
        detail = f"Loss = {loss}; expected >= 0" if not passed else "Non-negative as expected"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Perfect prediction yields zero loss
    # When y_pred == y_true, MSE should be exactly 0
    try:
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = y_true.copy()
        loss = fn(y_pred, y_true)
        passed = np.abs(loss) < 1e-6
        detail = f"Loss = {loss}; expected 0" if not passed else "Zero loss for perfect prediction"
        results.append({"name": "perfect_prediction_zero_loss", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "perfect_prediction_zero_loss", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling invariance of differences
    # MSE(c*y_pred, c*y_true) = c^2 * MSE(y_pred, y_true) for any scalar c
    try:
        y_pred = np.array([1.0, 2.0, 3.0])
        y_true = np.array([1.5, 2.5, 3.5])
        loss1 = fn(y_pred, y_true)
        
        c = 2.5
        loss2 = fn(c * y_pred, c * y_true)
        expected_loss2 = (c ** 2) * loss1
        
        passed = np.abs(loss2 - expected_loss2) < 1e-6
        detail = f"Loss2 = {loss2}, expected = {expected_loss2}" if not passed else "Scaling property holds"
        results.append({"name": "scaling_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 4: Permutation invariance
    # MSE is invariant to permutation of samples (order doesn't matter)
    try:
        np.random.seed(42)
        y_pred = np.array([1.2, 3.4, 2.1, 4.5, 0.9])
        y_true = np.array([1.0, 3.5, 2.0, 4.6, 1.1])
        loss1 = fn(y_pred, y_true)
        
        perm = np.array([4, 1, 0, 3, 2])
        loss2 = fn(y_pred[perm], y_true[perm])
        
        passed = np.abs(loss1 - loss2) < 1e-6
        detail = f"Loss1 = {loss1}, Loss2 = {loss2}" if not passed else "Permutation invariance holds"
        results.append({"name": "permutation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "permutation_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Known closed-form case
    # Single sample with known difference: MSE([2.0], [0.0]) = (2.0 - 0.0)^2 = 4.0
    try:
        y_pred = np.array([2.0])
        y_true = np.array([0.0])
        loss = fn(y_pred, y_true)
        expected = 4.0
        passed = np.abs(loss - expected) < 1e-6
        detail = f"Loss = {loss}, expected = {expected}" if not passed else "Closed-form case correct"
        results.append({"name": "closed_form_single_sample", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "closed_form_single_sample", "passed": False, "detail": str(e)})
    
    return results
