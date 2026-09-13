import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output dimension matches input dimension
    def test_output_dimension():
        try:
            d = 5
            grad_H_ij_xk = np.random.randn(d)
            grad_H_ij_wk = np.random.randn(d)
            grad_H_wk = np.random.randn(d)
            
            result = fn(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            
            assert isinstance(result, np.ndarray), "Output must be numpy array"
            assert result.ndim == 1, "Output must be 1-dimensional"
            assert result.shape[0] == d, f"Output dimension {result.shape[0]} != input dimension {d}"
            
            return True, "Output has correct dimension"
        except Exception as e:
            return False, str(e)
    
    # Test 2: Correctness of arithmetic formula g^k = ∇H_{i,j}(x^k) - ∇H_{i,j}(w^k) + ∇H(w^k)
    def test_arithmetic_formula():
        try:
            np.random.seed(42)
            d = 10
            grad_H_ij_xk = np.random.randn(d)
            grad_H_ij_wk = np.random.randn(d)
            grad_H_wk = np.random.randn(d)
            
            result = fn(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            expected = grad_H_ij_xk - grad_H_ij_wk + grad_H_wk
            
            assert np.allclose(result, expected, atol=1e-6), \
                f"Result {result} != expected {expected}"
            
            return True, "Arithmetic formula is correct"
        except Exception as e:
            return False, str(e)
    
    # Test 3: Zero input case - when all gradients are zero, output is zero
    def test_zero_input():
        try:
            d = 7
            grad_H_ij_xk = np.zeros(d)
            grad_H_ij_wk = np.zeros(d)
            grad_H_wk = np.zeros(d)
            
            result = fn(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            expected = np.zeros(d)
            
            assert np.allclose(result, expected, atol=1e-6), \
                f"Zero input should produce zero output, got {result}"
            
            return True, "Zero input produces zero output"
        except Exception as e:
            return False, str(e)
    
    # Test 4: Cancellation property - when grad_H_ij_xk == grad_H_ij_wk, output equals grad_H_wk
    def test_cancellation_property():
        try:
            np.random.seed(123)
            d = 8
            grad_H_ij_xk = np.random.randn(d)
            grad_H_ij_wk = grad_H_ij_xk.copy()  # Same as xk
            grad_H_wk = np.random.randn(d)
            
            result = fn(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            expected = grad_H_wk
            
            assert np.allclose(result, expected, atol=1e-6), \
                f"When grad_H_ij_xk == grad_H_ij_wk, output should equal grad_H_wk"
            
            return True, "Cancellation property holds"
        except Exception as e:
            return False, str(e)
    
    # Test 5: Linearity in each component - output is linear combination of inputs
    def test_linearity():
        try:
            np.random.seed(456)
            d = 6
            grad_H_ij_xk = np.random.randn(d)
            grad_H_ij_wk = np.random.randn(d)
            grad_H_wk = np.random.randn(d)
            
            result = fn(grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            
            # Test linearity: scaling first input by 2 should scale output by 2
            result_scaled = fn(2 * grad_H_ij_xk, grad_H_ij_wk, grad_H_wk)
            expected_scaled = 2 * grad_H_ij_xk - grad_H_ij_wk + grad_H_wk
            
            assert np.allclose(result_scaled, expected_scaled, atol=1e-6), \
                "Output should scale linearly with first input"
            
            return True, "Linearity property holds"
        except Exception as e:
            return False, str(e)
    
    # Run all tests
    tests = [
        ("Output dimension matches input", test_output_dimension),
        ("Arithmetic formula correctness", test_arithmetic_formula),
        ("Zero input produces zero output", test_zero_input),
        ("Cancellation property", test_cancellation_property),
        ("Linearity in components", test_linearity),
    ]
    
    for test_name, test_fn in tests:
        try:
            passed, detail = test_fn()
            results.append({"name": test_name, "passed": passed, "detail": detail})
        except Exception as e:
            results.append({"name": test_name, "passed": False, "detail": str(e)})
    
    return results
