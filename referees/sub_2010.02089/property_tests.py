import numpy as np

def check(fn):
    results = []
    
    # Test 1: Degenerate case - when all nodes are observed (k=0)
    try:
        n = 3
        R = np.array([[1.0, 0.5, 0.3],
                      [0.5, 1.0, 0.4],
                      [0.3, 0.4, 1.0]])
        z_obs = np.array([0.5, -0.3, 0.8])
        
        mu_cond, Sigma_cond = fn(R, z_obs)
        
        # When k=0, mu_cond should be empty and Sigma_cond should be (0,0)
        passed = (mu_cond.shape == (0,) and Sigma_cond.shape == (0, 0))
        results.append({
            "name": "Degenerate case: all nodes observed (k=0)",
            "passed": passed,
            "detail": f"Expected empty arrays, got mu_cond.shape={mu_cond.shape}, Sigma_cond.shape={Sigma_cond.shape}"
        })
    except Exception as e:
        results.append({
            "name": "Degenerate case: all nodes observed (k=0)",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Independence case - when observed and unobserved are independent
    try:
        # R_01 = 0 means independence
        R = np.array([[1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0],
                      [0.0, 0.0, 1.0]])
        z_obs = np.array([1.5, -0.8])  # m=2, k=1
        
        mu_cond, Sigma_cond = fn(R, z_obs)
        
        # When independent, mu_cond should be 0 and Sigma_cond should be R_11
        expected_mu = np.array([0.0])
        expected_Sigma = np.array([[1.0]])
        
        mu_close = np.allclose(mu_cond, expected_mu, atol=1e-6)
        sigma_close = np.allclose(Sigma_cond, expected_Sigma, atol=1e-6)
        passed = mu_close and sigma_close
        
        results.append({
            "name": "Independence: R_01=0 implies mu_cond=0, Sigma_cond=R_11",
            "passed": passed,
            "detail": f"mu_cond={mu_cond}, expected={expected_mu}, Sigma_cond={Sigma_cond}, expected={expected_Sigma}"
        })
    except Exception as e:
        results.append({
            "name": "Independence: R_01=0 implies mu_cond=0, Sigma_cond=R_11",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Conditional covariance is positive semi-definite
    try:
        np.random.seed(42)
        n = 5
        m = 3
        k = n - m
        
        # Generate a valid correlation matrix
        A = np.random.randn(n, n)
        R = A @ A.T
        D = np.sqrt(np.diag(R))
        R = R / D[:, None] / D[None, :]
        
        z_obs = np.random.randn(m)
        
        mu_cond, Sigma_cond = fn(R, z_obs)
        
        # Check that Sigma_cond is positive semi-definite (all eigenvalues >= 0)
        eigenvalues = np.linalg.eigvalsh(Sigma_cond)
        passed = np.all(eigenvalues >= -1e-6)
        
        results.append({
            "name": "Conditional covariance is positive semi-definite",
            "passed": passed,
            "detail": f"Min eigenvalue={np.min(eigenvalues)}, all eigenvalues={eigenvalues}"
        })
    except Exception as e:
        results.append({
            "name": "Conditional covariance is positive semi-definite",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Scaling property - scaling z_obs scales mu_cond linearly
    try:
        R = np.array([[1.0, 0.6, 0.4],
                      [0.6, 1.0, 0.5],
                      [0.4, 0.5, 1.0]])
        z_obs = np.array([0.5, -0.3])
        scale = 2.5
        
        mu_cond1, Sigma_cond1 = fn(R, z_obs)
        mu_cond2, Sigma_cond2 = fn(R, scale * z_obs)
        
        # mu_cond should scale linearly with z_obs
        # Sigma_cond should be unchanged (independent of z_obs)
        mu_scaled = np.allclose(mu_cond2, scale * mu_cond1, atol=1e-6)
        sigma_unchanged = np.allclose(Sigma_cond1, Sigma_cond2, atol=1e-6)
        passed = mu_scaled and sigma_unchanged
        
        results.append({
            "name": "Scaling: mu_cond scales linearly, Sigma_cond unchanged",
            "passed": passed,
            "detail": f"mu_cond1={mu_cond1}, mu_cond2={mu_cond2}, scale*mu_cond1={scale*mu_cond1}, Sigma unchanged={sigma_unchanged}"
        })
    except Exception as e:
        results.append({
            "name": "Scaling: mu_cond scales linearly, Sigma_cond unchanged",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Perfect correlation case
    try:
        # When R_01 = R_00^{1/2} @ R_11^{1/2}, conditional variance should be reduced
        R = np.array([[1.0, 0.9],
                      [0.9, 1.0]])
        z_obs = np.array([1.0])  # m=1, k=1
        
        mu_cond, Sigma_cond = fn(R, z_obs)
        
        # Analytical: mu_cond = 0.9 * 1.0 = 0.9
        # Sigma_cond = 1.0 - 0.9 * 1.0 * 0.9 = 0.19
        expected_mu = np.array([0.9])
        expected_Sigma = np.array([[0.19]])
        
        mu_close = np.allclose(mu_cond, expected_mu, atol=1e-6)
        sigma_close = np.allclose(Sigma_cond, expected_Sigma, atol=1e-6)
        passed = mu_close and sigma_close
        
        results.append({
            "name": "Perfect correlation: analytical verification",
            "passed": passed,
            "detail": f"mu_cond={mu_cond}, expected={expected_mu}, Sigma_cond={Sigma_cond}, expected={expected_Sigma}"
        })
    except Exception as e:
        results.append({
            "name": "Perfect correlation: analytical verification",
            "passed": False,
            "detail": str(e)
        })
    
    return results
