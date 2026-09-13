import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity
    # MSE is always non-negative by definition
    try:
        A_c = np.array([[0.0, 0.5], [0.5, 1.0]])
        A_c_prime = np.array([[0.1, 0.6], [0.4, 0.9]])
        loss = fn(A_c, A_c_prime)
        passed = loss >= 0.0
        detail = f"Loss = {loss}, expected >= 0.0" if not passed else "Non-negativity holds"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Identity property - identical matrices yield zero loss
    # When A_c == A_c_prime, MSE should be exactly 0
    try:
        A = np.array([[0.0, 0.3, 0.7], [0.3, 1.0, 0.2], [0.7, 0.2, 0.5]])
        loss = fn(A, A)
        passed = abs(loss) < 1e-10
        detail = f"Loss = {loss}, expected 0.0" if not passed else "Identity property holds"
        results.append({"name": "identity_property", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identity_property", "passed": False, "detail": str(e)})
    
    # Test 3: Size mismatch handling - uses min(N, N') overlap
    # Verify that only the overlapping region contributes to loss
    try:
        A_c = np.array([[1.0, 0.0], [0.0, 1.0]])  # 2x2
        A_c_prime = np.array([[1.0, 0.0, 0.5], [0.0, 1.0, 0.5], [0.5, 0.5, 0.0]])  # 3x3
        loss = fn(A_c, A_c_prime)
        # Expected: MSE over 2x2 region = sum((1-1)^2 + (0-0)^2 + (0-0)^2 + (1-1)^2) / 4 = 0
        passed = abs(loss) < 1e-10
        detail = f"Loss = {loss}, expected 0.0 for identical overlap" if not passed else "Size mismatch handled correctly"
        results.append({"name": "size_mismatch_overlap", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "size_mismatch_overlap", "passed": False, "detail": str(e)})
    
    # Test 4: Empty/zero-size matrix handling
    # When either matrix is empty or min_size is 0, return 0.0
    try:
        A_empty = np.array([]).reshape(0, 0)
        A_nonempty = np.array([[0.5, 0.5], [0.5, 0.5]])
        loss1 = fn(A_empty, A_nonempty)
        loss2 = fn(A_nonempty, A_empty)
        passed = abs(loss1) < 1e-10 and abs(loss2) < 1e-10
        detail = f"Losses = {loss1}, {loss2}, expected 0.0" if not passed else "Empty matrix case handled"
        results.append({"name": "empty_matrix_handling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "empty_matrix_handling", "passed": False, "detail": str(e)})
    
    # Test 5: Closed-form verification with known simple case
    # Compute MSE manually for a small known case
    try:
        A_c = np.array([[0.0, 1.0], [1.0, 0.0]])
        A_c_prime = np.array([[0.0, 0.0], [0.0, 0.0]])
        loss = fn(A_c, A_c_prime)
        # Expected: ((0-0)^2 + (1-0)^2 + (1-0)^2 + (0-0)^2) / 4 = 2/4 = 0.5
        expected = 0.5
        passed = abs(loss - expected) < 1e-6
        detail = f"Loss = {loss}, expected {expected}" if not passed else "Closed-form verification passed"
        results.append({"name": "closed_form_verification", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "closed_form_verification", "passed": False, "detail": str(e)})
    
    return results
