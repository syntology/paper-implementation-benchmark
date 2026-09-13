import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity property
    # Cross-entropy loss must always be non-negative since log_probs are log probabilities (≤ 0)
    # and we negate them. Loss = 0 only when all predictions are perfect (log_prob = 0 at true class)
    try:
        np.random.seed(42)
        n, C = 10, 5
        log_probs = np.log(np.random.dirichlet(np.ones(C), size=n))
        target_labels = np.random.randint(0, C, size=n)
        loss = fn(log_probs, target_labels)
        passed = loss >= -1e-6  # Allow small numerical error
        results.append({
            "name": "non_negativity",
            "passed": passed,
            "detail": f"Loss {loss} should be non-negative"
        })
    except Exception as e:
        results.append({
            "name": "non_negativity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Perfect prediction gives zero loss
    # When log_probs[i, target_labels[i]] = 0 for all i (probability = 1), loss should be 0
    try:
        n, C = 8, 4
        target_labels = np.array([0, 1, 2, 3, 0, 1, 2, 3])
        log_probs = np.full((n, C), -np.inf)
        for i in range(n):
            log_probs[i, target_labels[i]] = 0.0  # log(1) = 0
        loss = fn(log_probs, target_labels)
        passed = abs(loss) < 1e-6
        results.append({
            "name": "perfect_prediction_zero_loss",
            "passed": passed,
            "detail": f"Loss {loss} should be 0 for perfect predictions"
        })
    except Exception as e:
        results.append({
            "name": "perfect_prediction_zero_loss",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Sample permutation invariance
    # Permuting both log_probs rows and target_labels together should give same loss
    try:
        np.random.seed(123)
        n, C = 12, 6
        log_probs = np.log(np.random.dirichlet(np.ones(C), size=n))
        target_labels = np.random.randint(0, C, size=n)
        loss1 = fn(log_probs, target_labels)
        
        perm = np.random.permutation(n)
        log_probs_perm = log_probs[perm]
        target_labels_perm = target_labels[perm]
        loss2 = fn(log_probs_perm, target_labels_perm)
        
        passed = abs(loss1 - loss2) < 1e-6
        results.append({
            "name": "sample_permutation_invariance",
            "passed": passed,
            "detail": f"Loss before {loss1} and after permutation {loss2} should be equal"
        })
    except Exception as e:
        results.append({
            "name": "sample_permutation_invariance",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Known closed-form case - uniform wrong prediction
    # If log_probs[i, target_labels[i]] = log(p) for all i, then loss = -log(p)
    try:
        n, C = 10, 5
        p = 0.2  # probability
        log_p = np.log(p)
        target_labels = np.array([1, 2, 0, 3, 4, 1, 2, 0, 3, 4])
        log_probs = np.random.uniform(-5, -0.1, size=(n, C))
        for i in range(n):
            log_probs[i, target_labels[i]] = log_p
        
        loss = fn(log_probs, target_labels)
        expected_loss = -log_p
        passed = abs(loss - expected_loss) < 1e-6
        results.append({
            "name": "uniform_log_prob_closed_form",
            "passed": passed,
            "detail": f"Loss {loss} should equal -log(p) = {expected_loss}"
        })
    except Exception as e:
        results.append({
            "name": "uniform_log_prob_closed_form",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Linearity of expectation - loss on combined dataset equals average of losses
    # L(concat(A,B)) * (n_A + n_B) = L(A) * n_A + L(B) * n_B
    try:
        np.random.seed(456)
        n_A, n_B, C = 6, 4, 5
        log_probs_A = np.log(np.random.dirichlet(np.ones(C), size=n_A))
        target_labels_A = np.random.randint(0, C, size=n_A)
        log_probs_B = np.log(np.random.dirichlet(np.ones(C), size=n_B))
        target_labels_B = np.random.randint(0, C, size=n_B)
        
        loss_A = fn(log_probs_A, target_labels_A)
        loss_B = fn(log_probs_B, target_labels_B)
        
        log_probs_combined = np.vstack([log_probs_A, log_probs_B])
        target_labels_combined = np.concatenate([target_labels_A, target_labels_B])
        loss_combined = fn(log_probs_combined, target_labels_combined)
        
        expected_combined = (loss_A * n_A + loss_B * n_B) / (n_A + n_B)
        passed = abs(loss_combined - expected_combined) < 1e-6
        results.append({
            "name": "linearity_of_expectation",
            "passed": passed,
            "detail": f"Combined loss {loss_combined} should equal weighted average {expected_combined}"
        })
    except Exception as e:
        results.append({
            "name": "linearity_of_expectation",
            "passed": False,
            "detail": str(e)
        })
    
    return results
