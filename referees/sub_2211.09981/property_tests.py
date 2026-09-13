import numpy as np

def check(fn):
    results = []
    
    # Test 1: Cross-entropy is non-negative
    # Property: KL divergence (cross-entropy minus entropy) is always >= 0
    # Since cross-entropy = KL + H(p_teacher), and H(p_teacher) >= 0,
    # cross-entropy >= 0 for valid probability distributions
    def test_non_negative():
        try:
            np.random.seed(42)
            b, n, c = 4, 3, 8
            # Create valid log probabilities (normalized)
            log_ps = np.random.randn(b, n, c)
            log_ps = log_ps - np.logaddexp.reduce(log_ps, axis=2, keepdims=True)
            log_pt = np.random.randn(b, n, c)
            log_pt = log_pt - np.logaddexp.reduce(log_pt, axis=2, keepdims=True)
            
            for strategy in ['mean', 'entropy_weighted', 'max']:
                loss = fn(log_ps, log_pt, strategy)
                passed = loss >= -1e-6  # Allow small numerical error
                if not passed:
                    return False, f"Loss {loss} is negative for strategy {strategy}"
            return True, "All strategies produce non-negative loss"
        except Exception as e:
            return False, str(e)
    
    results.append({
        "name": "test_non_negative",
        "passed": test_non_negative()[0],
        "detail": test_non_negative()[1]
    })
    
    # Test 2: Uniform teacher distribution with identical student should give low loss
    # Property: When teacher and student are identical, cross-entropy equals entropy of teacher
    # When teacher is uniform over c classes, entropy = log(c), so loss should be log(c)
    def test_uniform_identical():
        try:
            np.random.seed(43)
            b, n, c = 2, 2, 4
            # Uniform distribution: log(1/c) for all classes
            log_uniform = np.full((b, n, c), -np.log(c))
            
            loss = fn(log_uniform, log_uniform, 'mean')
            expected = np.log(c)
            passed = np.abs(loss - expected) < 1e-5
            if not passed:
                return False, f"Expected {expected}, got {loss}"
            return True, f"Uniform identical case: loss={loss:.6f}, expected={expected:.6f}"
        except Exception as e:
            return False, str(e)
    
    results.append({
        "name": "test_uniform_identical",
        "passed": test_uniform_identical()[0],
        "detail": test_uniform_identical()[1]
    })
    
    # Test 3: Mean strategy is invariant to permutation of ensemble heads
    # Property: Averaging over heads means reordering heads doesn't change result
    def test_mean_head_permutation_invariant():
        try:
            np.random.seed(44)
            b, n, c = 3, 4, 5
            log_ps = np.random.randn(b, n, c)
            log_ps = log_ps - np.logaddexp.reduce(log_ps, axis=2, keepdims=True)
            log_pt = np.random.randn(b, n, c)
            log_pt = log_pt - np.logaddexp.reduce(log_pt, axis=2, keepdims=True)
            
            loss_original = fn(log_ps, log_pt, 'mean')
            
            # Permute heads
            perm = np.array([2, 0, 3, 1])
            log_ps_perm = log_ps[:, perm, :]
            log_pt_perm = log_pt[:, perm, :]
            loss_permuted = fn(log_ps_perm, log_pt_perm, 'mean')
            
            passed = np.abs(loss_original - loss_permuted) < 1e-5
            if not passed:
                return False, f"Original {loss_original} != Permuted {loss_permuted}"
            return True, f"Mean strategy is permutation invariant"
        except Exception as e:
            return False, str(e)
    
    results.append({
        "name": "test_mean_head_permutation_invariant",
        "passed": test_mean_head_permutation_invariant()[0],
        "detail": test_mean_head_permutation_invariant()[1]
    })
    
    # Test 4: Max strategy selects the head with highest max log probability
    # Property: When one head has much higher max probability than others,
    # max strategy should produce loss close to that head's loss
    def test_max_strategy_selection():
        try:
            np.random.seed(45)
            b, n, c = 2, 3, 4
            
            # Create log probabilities where head 1 is clearly better (higher max)
            log_ps = np.random.randn(b, n, c) - 5  # Low values
            log_pt = np.random.randn(b, n, c) - 5
            
            # Make head 1 have much higher max log probability
            log_pt[:, 1, :] = np.random.randn(b, c) + 2  # Higher values
            log_ps[:, 1, :] = np.random.randn(b, c) + 2
            
            loss_max = fn(log_ps, log_pt, 'max')
            
            # Manually compute loss for head 1 only
            pt_probs = np.exp(log_pt[:, 1, :])
            expected_loss = -np.mean(np.sum(pt_probs * log_ps[:, 1, :], axis=1))
            
            passed = np.abs(loss_max - expected_loss) < 1e-5
            if not passed:
                return False, f"Max loss {loss_max} != expected {expected_loss}"
            return True, f"Max strategy correctly selects best head"
        except Exception as e:
            return False, str(e)
    
    results.append({
        "name": "test_max_strategy_selection",
        "passed": test_max_strategy_selection()[0],
        "detail": test_max_strategy_selection()[1]
    })
    
    # Test 5: Entropy-weighted strategy weights are normalized and positive
    # Property: Weights should sum to 1 and be positive (exp of any real number)
    # When all heads have equal entropy, weights should be equal
    def test_entropy_weighted_normalization():
        try:
            np.random.seed(46)
            b, n, c = 3, 4, 5
            
            # Create identical distributions for all heads (equal entropy)
            log_uniform = np.full((b, n, c), -np.log(c))
            
            loss_entropy = fn(log_uniform, log_uniform, 'entropy_weighted')
            loss_mean = fn(log_uniform, log_uniform, 'mean')
            
            # When all heads have equal entropy, entropy_weighted should equal mean
            passed = np.abs(loss_entropy - loss_mean) < 1e-5
            if not passed:
                return False, f"Entropy-weighted {loss_entropy} != mean {loss_mean} for uniform case"
            return True, f"Entropy-weighted equals mean for uniform entropy case"
        except Exception as e:
            return False, str(e)
    
    results.append({
        "name": "test_entropy_weighted_normalization",
        "passed": test_entropy_weighted_normalization()[0],
        "detail": test_entropy_weighted_normalization()[1]
    })
    
    return results
