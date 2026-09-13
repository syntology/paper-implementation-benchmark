import numpy as np

def check(fn):
    results = []
    
    # Test 1: Bounds - proportion should be in [0, 1] when beta <= loss_j <= alpha
    try:
        passed = True
        detail = ""
        test_cases = [
            (10.0, 5.0, 2.0),  # loss_j in middle
            (10.0, 10.0, 2.0),  # loss_j at alpha (should give 0)
            (10.0, 2.0, 2.0),   # loss_j at beta (should give 1)
            (5.0, 3.5, 1.0),    # another middle case
        ]
        for alpha, loss_j, beta in test_cases:
            result = fn(loss_j, alpha, beta)
            if not (0.0 <= result <= 1.0 + 1e-6):
                passed = False
                detail = f"Proportion {result} out of [0,1] for loss_j={loss_j}, alpha={alpha}, beta={beta}"
                break
        if passed:
            detail = "All valid inputs produce proportions in [0, 1]"
        results.append({"name": "Bounds: proportion in [0, 1] for beta <= loss_j <= alpha", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Bounds: proportion in [0, 1] for beta <= loss_j <= alpha", "passed": False, "detail": str(e)})
    
    # Test 2: Limiting case - loss_j = alpha should give proportion = 0
    try:
        passed = True
        detail = ""
        test_cases = [
            (10.0, 10.0, 2.0),
            (5.0, 5.0, 1.0),
            (100.0, 100.0, 50.0),
        ]
        for alpha, loss_j, beta in test_cases:
            result = fn(loss_j, alpha, beta)
            if not np.abs(result - 0.0) < 1e-6:
                passed = False
                detail = f"Expected 0.0, got {result} for loss_j=alpha={alpha}, beta={beta}"
                break
        if passed:
            detail = "loss_j = alpha correctly gives proportion = 0"
        results.append({"name": "Limiting case: loss_j = alpha => proportion = 0", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Limiting case: loss_j = alpha => proportion = 0", "passed": False, "detail": str(e)})
    
    # Test 3: Limiting case - loss_j = beta should give proportion = 1
    try:
        passed = True
        detail = ""
        test_cases = [
            (10.0, 2.0, 2.0),
            (5.0, 1.0, 1.0),
            (100.0, 50.0, 50.0),
        ]
        for alpha, loss_j, beta in test_cases:
            result = fn(loss_j, alpha, beta)
            if not np.abs(result - 1.0) < 1e-6:
                passed = False
                detail = f"Expected 1.0, got {result} for loss_j=beta={loss_j}, alpha={alpha}"
                break
        if passed:
            detail = "loss_j = beta correctly gives proportion = 1"
        results.append({"name": "Limiting case: loss_j = beta => proportion = 1", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Limiting case: loss_j = beta => proportion = 1", "passed": False, "detail": str(e)})
    
    # Test 4: Translation invariance - adding constant to all three values doesn't change proportion
    try:
        passed = True
        detail = ""
        np.random.seed(42)
        base_cases = [
            (10.0, 6.0, 2.0),
            (5.0, 3.0, 1.0),
            (20.0, 15.0, 10.0),
        ]
        translations = [0.0, 5.0, -3.0, 100.0]
        for alpha, loss_j, beta in base_cases:
            base_result = fn(loss_j, alpha, beta)
            for t in translations:
                translated_result = fn(loss_j + t, alpha + t, beta + t)
                if not np.abs(base_result - translated_result) < 1e-6:
                    passed = False
                    detail = f"Translation invariance failed: base={base_result}, translated={translated_result}, t={t}"
                    break
            if not passed:
                break
        if passed:
            detail = "Proportion invariant under uniform translation of all parameters"
        results.append({"name": "Translation invariance: P(ℓ_j) unchanged by adding constant to all inputs", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Translation invariance: P(ℓ_j) unchanged by adding constant to all inputs", "passed": False, "detail": str(e)})
    
    # Test 5: Scaling invariance - multiplying all three values by positive constant doesn't change proportion
    try:
        passed = True
        detail = ""
        np.random.seed(42)
        base_cases = [
            (10.0, 6.0, 2.0),
            (5.0, 3.0, 1.0),
            (20.0, 15.0, 10.0),
        ]
        scales = [0.5, 2.0, 10.0, 0.1]
        for alpha, loss_j, beta in base_cases:
            base_result = fn(loss_j, alpha, beta)
            for s in scales:
                scaled_result = fn(loss_j * s, alpha * s, beta * s)
                if not np.abs(base_result - scaled_result) < 1e-6:
                    passed = False
                    detail = f"Scaling invariance failed: base={base_result}, scaled={scaled_result}, scale={s}"
                    break
            if not passed:
                break
        if passed:
            detail = "Proportion invariant under uniform positive scaling of all parameters"
        results.append({"name": "Scaling invariance: P(ℓ_j) unchanged by multiplying all inputs by positive constant", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Scaling invariance: P(ℓ_j) unchanged by multiplying all inputs by positive constant", "passed": False, "detail": str(e)})
    
    return results
