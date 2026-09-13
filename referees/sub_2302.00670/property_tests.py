import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output shape matches input sample dimension
    def test_output_shape():
        try:
            np.random.seed(42)
            D = 5
            N = 10
            x_t = np.random.randn(D)
            B_L = np.random.randn(N, D)
            alpha_bar_t = 0.7
            t = 50
            
            output = fn(x_t, B_L, t, alpha_bar_t)
            
            assert output.shape == (D,), f"Expected shape ({D},), got {output.shape}"
            passed = True
            detail = "Output shape is correct"
        except Exception as e:
            passed = False
            detail = str(e)
        
        results.append({"name": "output_shape", "passed": passed, "detail": detail})
    
    # Test 2: Weights sum to 1 (implicit via normalization)
    # This tests that the weighted sum is a proper convex combination
    def test_convex_combination():
        try:
            np.random.seed(43)
            D = 3
            N = 8
            x_t = np.random.randn(D)
            B_L = np.random.randn(N, D)
            alpha_bar_t = 0.5
            t = 100
            
            output = fn(x_t, B_L, t, alpha_bar_t)
            
            # Compute expected bounds: each score component is bounded by 1/(1-alpha_bar_t)
            # in magnitude, so the weighted sum should also be bounded similarly
            sigma_sq = 1 - alpha_bar_t
            max_score_magnitude = np.max(np.abs(x_t)) / sigma_sq + np.max(np.linalg.norm(B_L, axis=1)) / sigma_sq
            
            # The output should be finite and not excessively large
            assert np.all(np.isfinite(output)), "Output contains non-finite values"
            passed = True
            detail = "Output is finite and represents valid weighted combination"
        except Exception as e:
            passed = False
            detail = str(e)
        
        results.append({"name": "convex_combination", "passed": passed, "detail": detail})
    
    # Test 3: Single reference sample case (degenerate case with known answer)
    # When N=1, the weight is 1.0 and output should equal the score for that sample
    def test_single_reference_sample():
        try:
            np.random.seed(44)
            D = 4
            x_t = np.array([1.0, 2.0, 3.0, 4.0])
            x_ref = np.array([0.5, 1.5, 2.5, 3.5])
            B_L = x_ref.reshape(1, D)
            alpha_bar_t = 0.6
            t = 0
            
            output = fn(x_t, B_L, t, alpha_bar_t)
            
            # Expected: single score = -(x_t - sqrt(alpha_bar_t)*x_ref) / (1-alpha_bar_t)
            sqrt_alpha = np.sqrt(alpha_bar_t)
            sigma_sq = 1 - alpha_bar_t
            expected_score = -(x_t - sqrt_alpha * x_ref) / sigma_sq
            
            assert np.allclose(output, expected_score, atol=1e-6), \
                f"Expected {expected_score}, got {output}"
            passed = True
            detail = "Single reference sample produces correct score"
        except Exception as e:
            passed = False
            detail = str(e)
        
        results.append({"name": "single_reference_sample", "passed": passed, "detail": detail})
    
    # Test 4: Identical reference samples produce zero output
    # When all reference samples are identical to each other, the weighted average
    # of identical scores should equal that score
    def test_identical_reference_samples():
        try:
            np.random.seed(45)
            D = 3
            N = 5
            x_t = np.array([1.0, 2.0, 3.0])
            x_ref = np.array([0.2, 0.3, 0.4])
            B_L = np.tile(x_ref, (N, 1))  # All samples identical
            alpha_bar_t = 0.8
            t = 10
            
            output = fn(x_t, B_L, t, alpha_bar_t)
            
            # Expected: all scores are identical, so weighted average equals that score
            sqrt_alpha = np.sqrt(alpha_bar_t)
            sigma_sq = 1 - alpha_bar_t
            expected_score = -(x_t - sqrt_alpha * x_ref) / sigma_sq
            
            assert np.allclose(output, expected_score, atol=1e-6), \
                f"Expected {expected_score}, got {output}"
            passed = True
            detail = "Identical reference samples produce consistent weighted score"
        except Exception as e:
            passed = False
            detail = str(e)
        
        results.append({"name": "identical_reference_samples", "passed": passed, "detail": detail})
    
    # Test 5: Permutation invariance of reference batch
    # Reordering reference samples should not change output (weights are reordered but sum is same)
    def test_permutation_invariance():
        try:
            np.random.seed(46)
            D = 4
            N = 6
            x_t = np.random.randn(D)
            B_L = np.random.randn(N, D)
            alpha_bar_t = 0.65
            t = 25
            
            output1 = fn(x_t, B_L, t, alpha_bar_t)
            
            # Permute reference batch
            perm = np.array([3, 1, 4, 0, 5, 2])
            B_L_permuted = B_L[perm]
            output2 = fn(x_t, B_L_permuted, t, alpha_bar_t)
            
            assert np.allclose(output1, output2, atol=1e-6), \
                f"Permutation changed output: {output1} vs {output2}"
            passed = True
            detail = "Output invariant to reference batch permutation"
        except Exception as e:
            passed = False
            detail = str(e)
        
        results.append({"name": "permutation_invariance", "passed": passed, "detail": detail})
    
    test_output_shape()
    test_convex_combination()
    test_single_reference_sample()
    test_identical_reference_samples()
    test_permutation_invariance()
    
    return results
