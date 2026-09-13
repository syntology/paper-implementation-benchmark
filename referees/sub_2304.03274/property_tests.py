import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity property
    # The sum of squared L2 norms must always be non-negative
    try:
        np.random.seed(42)
        states = np.random.randn(10, 5)
        reference_states = np.random.randn(10, 5)
        loss = fn(states, reference_states)
        passed = loss >= 0
        detail = f"Loss = {loss}, expected >= 0"
        results.append({"name": "non_negativity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Zero loss for identical inputs
    # When states == reference_states, loss should be exactly 0
    try:
        np.random.seed(43)
        states = np.random.randn(8, 4)
        reference_states = states.copy()
        loss = fn(states, reference_states)
        passed = abs(loss) < 1e-6
        detail = f"Loss = {loss}, expected 0 for identical inputs"
        results.append({"name": "zero_loss_identical", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_loss_identical", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling property
    # Loss should scale quadratically: L(alpha*s, alpha*r) = alpha^2 * L(s, r)
    try:
        np.random.seed(44)
        states = np.random.randn(6, 3)
        reference_states = np.random.randn(6, 3)
        alpha = 2.5
        
        loss_original = fn(states, reference_states)
        loss_scaled = fn(alpha * states, alpha * reference_states)
        expected_scaled = alpha**2 * loss_original
        
        passed = abs(loss_scaled - expected_scaled) < 1e-6
        detail = f"Scaled loss = {loss_scaled}, expected {expected_scaled}"
        results.append({"name": "quadratic_scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "quadratic_scaling", "passed": False, "detail": str(e)})
    
    # Test 4: Translation invariance
    # L(s + c, r + c) = L(s, r) for any constant vector c
    try:
        np.random.seed(45)
        states = np.random.randn(7, 4)
        reference_states = np.random.randn(7, 4)
        translation = np.array([1.5, -2.0, 3.5, -1.0])
        
        loss_original = fn(states, reference_states)
        loss_translated = fn(states + translation, reference_states + translation)
        
        passed = abs(loss_original - loss_translated) < 1e-6
        detail = f"Original loss = {loss_original}, translated loss = {loss_translated}"
        results.append({"name": "translation_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Known closed-form case
    # For simple inputs, verify exact computation
    try:
        states = np.array([[1.0, 2.0], [3.0, 4.0]])
        reference_states = np.array([[0.0, 0.0], [1.0, 1.0]])
        # t=0: (1-0)^2 + (2-0)^2 = 1 + 4 = 5
        # t=1: (3-1)^2 + (4-1)^2 = 4 + 9 = 13
        # Total: 5 + 13 = 18
        expected_loss = 18.0
        
        loss = fn(states, reference_states)
        passed = abs(loss - expected_loss) < 1e-6
        detail = f"Loss = {loss}, expected {expected_loss}"
        results.append({"name": "known_closed_form", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "known_closed_form", "passed": False, "detail": str(e)})
    
    return results
