import numpy as np

def check(fn):
    results = []
    
    # Test 1: Non-negativity property
    # The diversity loss must always be non-negative since it's a ratio of norms
    try:
        np.random.seed(42)
        x = np.random.randn(3, 4, 5)
        x_prime = np.random.randn(3, 4, 5)
        t = np.random.randn(3, 4, 5)
        t_prime = np.random.randn(3, 4, 5)
        
        result = fn(x, x_prime, t, t_prime)
        passed = result >= 0 or result == np.inf
        results.append({
            "name": "Non-negativity property",
            "passed": passed,
            "detail": f"Result {result} should be non-negative or inf"
        })
    except Exception as e:
        results.append({
            "name": "Non-negativity property",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Scaling invariance in numerator and denominator
    # L_div(x, x', t, t') = L_div(k*x, k*x', m*t, m*t') for positive scalars k, m
    # because ||k*x - k*x'|| / ||m*t - m*t'|| = k*||x - x'|| / (m*||t - t'||)
    # Actually this is NOT invariant, so let's test the correct scaling property:
    # L_div(k*x, k*x', t, t') = k * L_div(x, x', t, t')
    try:
        np.random.seed(43)
        x = np.random.randn(2, 3, 4)
        x_prime = np.random.randn(2, 3, 4)
        t = np.random.randn(2, 3, 4)
        t_prime = np.random.randn(2, 3, 4)
        
        k = 2.5
        result_original = fn(x, x_prime, t, t_prime)
        result_scaled = fn(k * x, k * x_prime, t, t_prime)
        
        expected = k * result_original
        passed = np.abs(result_scaled - expected) < 1e-6
        results.append({
            "name": "Numerator scaling property",
            "passed": passed,
            "detail": f"Scaled result {result_scaled} vs expected {expected}"
        })
    except Exception as e:
        results.append({
            "name": "Numerator scaling property",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Zero denominator returns inf
    # When t == t_prime, denominator is zero and should return inf
    try:
        np.random.seed(44)
        x = np.random.randn(2, 3)
        x_prime = np.random.randn(2, 3)
        t = np.random.randn(2, 3)
        t_prime = t.copy()  # Make them identical
        
        result = fn(x, x_prime, t, t_prime)
        passed = result == np.inf
        results.append({
            "name": "Zero denominator returns inf",
            "passed": passed,
            "detail": f"Result {result} should be inf when t == t_prime"
        })
    except Exception as e:
        results.append({
            "name": "Zero denominator returns inf",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Zero numerator returns zero
    # When x == x_prime, numerator is zero and result should be 0
    try:
        np.random.seed(45)
        x = np.random.randn(3, 3)
        x_prime = x.copy()  # Make them identical
        t = np.random.randn(3, 3)
        t_prime = np.random.randn(3, 3)
        
        result = fn(x, x_prime, t, t_prime)
        passed = np.abs(result - 0.0) < 1e-6
        results.append({
            "name": "Zero numerator returns zero",
            "passed": passed,
            "detail": f"Result {result} should be 0 when x == x_prime"
        })
    except Exception as e:
        results.append({
            "name": "Zero numerator returns zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Symmetry property
    # L_div(x, x', t, t') = L_div(x', x, t', t) due to symmetry of norms
    try:
        np.random.seed(46)
        x = np.random.randn(4, 5)
        x_prime = np.random.randn(4, 5)
        t = np.random.randn(4, 5)
        t_prime = np.random.randn(4, 5)
        
        result1 = fn(x, x_prime, t, t_prime)
        result2 = fn(x_prime, x, t_prime, t)
        
        passed = np.abs(result1 - result2) < 1e-6
        results.append({
            "name": "Symmetry property",
            "passed": passed,
            "detail": f"L_div(x,x',t,t')={result1} vs L_div(x',x,t',t)={result2}"
        })
    except Exception as e:
        results.append({
            "name": "Symmetry property",
            "passed": False,
            "detail": str(e)
        })
    
    return results
