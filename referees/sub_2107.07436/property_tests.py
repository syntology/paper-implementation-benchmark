import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity of loss
    # The loss is a sum of squared terms plus a non-negative penalty, so it must be >= 0
    def test_non_negativity():
        try:
            np.random.seed(42)
            d = 5
            m = 10
            phi_hat = np.random.randn(d)
            v_all = 1.0
            v_empty = 0.0
            v_samples = np.random.randn(m)
            s_samples = np.random.randint(0, 2, size=(m, d)).astype(float)
            gamma = 0.5
            
            loss = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, False)
            
            passed = loss >= -1e-6  # Allow tiny numerical error
            detail = f"Loss = {loss}, expected >= 0"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "non_negativity_of_loss", "passed": test_non_negativity()[0], "detail": test_non_negativity()[1]})
    
    # Test 2: Efficiency penalty is zero when phi_hat sums to v_all - v_empty
    # When phi_hat already satisfies the efficiency constraint, the penalty term should be 0
    def test_efficiency_constraint_satisfied():
        try:
            np.random.seed(43)
            d = 5
            m = 8
            v_all = 2.0
            v_empty = 0.5
            target_sum = v_all - v_empty
            
            # Create phi_hat that sums to exactly target_sum
            phi_hat = np.random.randn(d)
            phi_hat = phi_hat * (target_sum / np.sum(phi_hat))
            
            v_samples = np.random.randn(m)
            s_samples = np.random.randint(0, 2, size=(m, d)).astype(float)
            gamma = 1.0
            
            loss_with_penalty = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, False)
            
            # Compute loss without penalty (gamma=0)
            loss_without_penalty = fn(phi_hat, v_all, v_empty, v_samples, s_samples, 0.0, False)
            
            # They should be equal when efficiency constraint is satisfied
            passed = np.abs(loss_with_penalty - loss_without_penalty) < 1e-6
            detail = f"Loss with penalty={loss_with_penalty}, without penalty={loss_without_penalty}, diff={abs(loss_with_penalty - loss_without_penalty)}"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "efficiency_constraint_satisfied", "passed": test_efficiency_constraint_satisfied()[0], "detail": test_efficiency_constraint_satisfied()[1]})
    
    # Test 3: Normalization reduces efficiency penalty
    # When normalize=True, phi_hat is adjusted to satisfy efficiency, so penalty should be 0
    def test_normalization_eliminates_penalty():
        try:
            np.random.seed(44)
            d = 5
            m = 8
            v_all = 3.0
            v_empty = 0.2
            
            # Create arbitrary phi_hat that doesn't satisfy efficiency
            phi_hat = np.random.randn(d)
            
            v_samples = np.random.randn(m)
            s_samples = np.random.randint(0, 2, size=(m, d)).astype(float)
            gamma = 2.0
            
            loss_normalized = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, True)
            loss_unnormalized = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, False)
            
            # Normalized loss should be <= unnormalized loss (penalty is reduced to 0)
            passed = loss_normalized <= loss_unnormalized + 1e-6
            detail = f"Normalized loss={loss_normalized}, unnormalized={loss_unnormalized}"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "normalization_reduces_penalty", "passed": test_normalization_eliminates_penalty()[0], "detail": test_normalization_eliminates_penalty()[1]})
    
    # Test 4: Gamma scaling property
    # Loss should scale linearly with gamma for the penalty term
    def test_gamma_scaling():
        try:
            np.random.seed(45)
            d = 4
            m = 6
            phi_hat = np.random.randn(d)
            v_all = 1.5
            v_empty = 0.3
            v_samples = np.random.randn(m)
            s_samples = np.random.randint(0, 2, size=(m, d)).astype(float)
            
            gamma1 = 0.5
            gamma2 = 2.0
            
            loss1 = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma1, False)
            loss2 = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma2, False)
            
            # The difference in losses should be proportional to the difference in gammas
            # loss2 - loss1 = (gamma2 - gamma1) * efficiency_penalty
            efficiency_penalty = (v_all - v_empty - np.sum(phi_hat)) ** 2
            expected_diff = (gamma2 - gamma1) * efficiency_penalty
            actual_diff = loss2 - loss1
            
            passed = np.abs(actual_diff - expected_diff) < 1e-6
            detail = f"Expected diff={expected_diff}, actual diff={actual_diff}"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "gamma_scaling_property", "passed": test_gamma_scaling()[0], "detail": test_gamma_scaling()[1]})
    
    # Test 5: Perfect prediction case
    # When phi_hat perfectly predicts all samples and satisfies efficiency, loss should be 0
    def test_perfect_prediction():
        try:
            np.random.seed(46)
            d = 4
            m = 5
            v_all = 2.0
            v_empty = 0.0
            
            # Create phi_hat that sums to v_all - v_empty
            phi_hat = np.ones(d) * (v_all - v_empty) / d
            
            # Create samples where v_samples = v_empty + dot(s_samples, phi_hat)
            s_samples = np.random.randint(0, 2, size=(m, d)).astype(float)
            v_samples = v_empty + np.dot(s_samples, phi_hat)
            
            gamma = 1.0
            
            loss = fn(phi_hat, v_all, v_empty, v_samples, s_samples, gamma, False)
            
            # Loss should be 0 (no approximation error, no efficiency penalty)
            passed = np.abs(loss) < 1e-6
            detail = f"Loss = {loss}, expected 0"
            return passed, detail
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "perfect_prediction_zero_loss", "passed": test_perfect_prediction()[0], "detail": test_perfect_prediction()[1]})
    
    return results
