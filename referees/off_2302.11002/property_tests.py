import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shapes are correct
    def test_output_shapes():
        try:
            np.random.seed(42)
            n, m = 5, 3
            mu = np.random.randn(n)
            Sigma = np.eye(n) + 0.1 * np.random.randn(n, n)
            Sigma = (Sigma + Sigma.T) / 2  # Make symmetric
            G = np.random.randn(m, n)
            b = np.random.randn(m)
            sigma_G = 0.5
            
            tilde_mu, tilde_Sigma = fn(mu, Sigma, G, b, sigma_G)
            
            assert tilde_mu.shape == (n,), f"Expected tilde_mu shape {(n,)}, got {tilde_mu.shape}"
            assert tilde_Sigma.shape == (n, n), f"Expected tilde_Sigma shape {(n, n)}, got {tilde_Sigma.shape}"
            return True, "Output shapes correct"
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "test_output_shapes", "passed": test_output_shapes()[0], "detail": test_output_shapes()[1]})
    
    # Test 2: Posterior covariance is symmetric and positive semi-definite
    def test_covariance_properties():
        try:
            np.random.seed(43)
            n, m = 4, 2
            mu = np.random.randn(n)
            Sigma = np.eye(n) + 0.1 * np.random.randn(n, n)
            Sigma = (Sigma + Sigma.T) / 2
            Sigma = Sigma + n * np.eye(n)  # Ensure positive definite
            G = np.random.randn(m, n)
            b = np.random.randn(m)
            sigma_G = 0.5
            
            tilde_mu, tilde_Sigma = fn(mu, Sigma, G, b, sigma_G)
            
            # Check symmetry
            assert np.allclose(tilde_Sigma, tilde_Sigma.T, atol=1e-6), "tilde_Sigma is not symmetric"
            
            # Check positive semi-definiteness via eigenvalues
            eigvals = np.linalg.eigvalsh(tilde_Sigma)
            assert np.all(eigvals >= -1e-6), f"tilde_Sigma has negative eigenvalues: {eigvals}"
            
            return True, "Covariance is symmetric and PSD"
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "test_covariance_properties", "passed": test_covariance_properties()[0], "detail": test_covariance_properties()[1]})
    
    # Test 3: Posterior covariance is smaller than prior (information gain)
    def test_covariance_reduction():
        try:
            np.random.seed(44)
            n, m = 4, 2
            mu = np.random.randn(n)
            Sigma = np.eye(n) + 0.1 * np.random.randn(n, n)
            Sigma = (Sigma + Sigma.T) / 2
            Sigma = Sigma + n * np.eye(n)
            G = np.random.randn(m, n)
            b = np.random.randn(m)
            sigma_G = 0.5
            
            tilde_mu, tilde_Sigma = fn(mu, Sigma, G, b, sigma_G)
            
            # Difference should be positive semi-definite (Sigma - tilde_Sigma >= 0)
            diff = Sigma - tilde_Sigma
            eigvals = np.linalg.eigvalsh(diff)
            assert np.all(eigvals >= -1e-6), f"Posterior covariance not smaller than prior: {eigvals}"
            
            return True, "Posterior covariance reduced (information gain)"
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "test_covariance_reduction", "passed": test_covariance_reduction()[0], "detail": test_covariance_reduction()[1]})
    
    # Test 4: Zero constraint noise recovers exact constraint satisfaction
    def test_zero_noise_limit():
        try:
            np.random.seed(45)
            n, m = 5, 2
            mu = np.random.randn(n)
            Sigma = np.eye(n) + 0.05 * np.random.randn(n, n)
            Sigma = (Sigma + Sigma.T) / 2
            Sigma = Sigma + n * np.eye(n)
            G = np.random.randn(m, n)
            b = np.random.randn(m)
            sigma_G = 1e-8  # Near-zero noise
            
            tilde_mu, tilde_Sigma = fn(mu, Sigma, G, b, sigma_G)
            
            # With zero noise, posterior mean should satisfy constraints exactly
            constraint_residual = np.linalg.norm(G @ tilde_mu - b)
            assert constraint_residual < 1e-4, f"Constraint not satisfied: residual = {constraint_residual}"
            
            return True, "Zero noise limit satisfies constraints"
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "test_zero_noise_limit", "passed": test_zero_noise_limit()[0], "detail": test_zero_noise_limit()[1]})
    
    # Test 5: No constraints (m=0) returns prior unchanged
    def test_no_constraints():
        try:
            np.random.seed(46)
            n = 5
            mu = np.random.randn(n)
            Sigma = np.eye(n) + 0.1 * np.random.randn(n, n)
            Sigma = (Sigma + Sigma.T) / 2
            Sigma = Sigma + n * np.eye(n)
            G = np.empty((0, n))  # No constraints
            b = np.empty(0)
            sigma_G = 0.5
            
            tilde_mu, tilde_Sigma = fn(mu, Sigma, G, b, sigma_G)
            
            # With no constraints, posterior should equal prior
            assert np.allclose(tilde_mu, mu, atol=1e-6), "Mean changed with no constraints"
            assert np.allclose(tilde_Sigma, Sigma, atol=1e-6), "Covariance changed with no constraints"
            
            return True, "No constraints returns prior"
        except Exception as e:
            return False, str(e)
    
    results.append({"name": "test_no_constraints", "passed": test_no_constraints()[0], "detail": test_no_constraints()[1]})
    
    return results
