import numpy as np

def check(fn):
    results = []
    
    # Test 1: Query scaling property
    # Scaling Q_prime by a constant should scale the output by the same constant
    try:
        np.random.seed(42)
        L, M, d = 5, 4, 3
        Q_prime = np.random.randn(L, M)
        K_prime = np.random.randn(L, M)
        V = np.random.randn(L, d)
        scale = 2.5
        
        output1 = fn(Q_prime, K_prime, V, is_bidirectional=True)
        output2 = fn(scale * Q_prime, K_prime, V, is_bidirectional=True)
        
        passed = np.allclose(scale * output1, output2, atol=1e-6, rtol=1e-6)
        results.append({
            "name": "Query scaling property (bidirectional)",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(scale * output1 - output2))}"
        })
    except Exception as e:
        results.append({
            "name": "Query scaling property (bidirectional)",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Uniform keys and values (bidirectional case)
    # When K_prime and V are constant across positions, output should be constant
    try:
        np.random.seed(43)
        L, M, d = 6, 4, 3
        k_vec = np.random.randn(M)
        v_vec = np.random.randn(d)
        K_prime = np.tile(k_vec, (L, 1))
        V = np.tile(v_vec, (L, 1))
        Q_prime = np.random.randn(L, M)
        
        output = fn(Q_prime, K_prime, V, is_bidirectional=True)
        
        # All rows should be identical to v_vec
        expected = np.tile(v_vec, (L, 1))
        passed = np.allclose(output, expected, atol=1e-6, rtol=1e-6)
        results.append({
            "name": "Uniform keys and values (bidirectional)",
            "passed": passed,
            "detail": f"Max diff from uniform: {np.max(np.abs(output - expected))}"
        })
    except Exception as e:
        results.append({
            "name": "Uniform keys and values (bidirectional)",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Single position sequence
    # For L=1, both bidirectional and unidirectional should give the same result
    try:
        np.random.seed(44)
        L, M, d = 1, 4, 3
        Q_prime = np.random.randn(L, M)
        K_prime = np.random.randn(L, M)
        V = np.random.randn(L, d)
        
        output_bidir = fn(Q_prime, K_prime, V, is_bidirectional=True)
        output_unidir = fn(Q_prime, K_prime, V, is_bidirectional=False)
        
        passed = np.allclose(output_bidir, output_unidir, atol=1e-6, rtol=1e-6)
        results.append({
            "name": "Single position equivalence",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(output_bidir - output_unidir))}"
        })
    except Exception as e:
        results.append({
            "name": "Single position equivalence",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Causal masking property
    # In unidirectional mode, output at position i should not depend on positions j > i
    try:
        np.random.seed(45)
        L, M, d = 5, 4, 3
        Q_prime = np.random.randn(L, M)
        K_prime = np.random.randn(L, M)
        V = np.random.randn(L, d)
        
        output1 = fn(Q_prime, K_prime, V, is_bidirectional=False)
        
        # Modify future positions (last 2 positions)
        K_prime_modified = K_prime.copy()
        V_modified = V.copy()
        K_prime_modified[-2:] = np.random.randn(2, M)
        V_modified[-2:] = np.random.randn(2, d)
        
        output2 = fn(Q_prime, K_prime_modified, V_modified, is_bidirectional=False)
        
        # First L-2 positions should be unchanged
        passed = np.allclose(output1[:-2], output2[:-2], atol=1e-6, rtol=1e-6)
        results.append({
            "name": "Causal masking property",
            "passed": passed,
            "detail": f"Max diff in past positions: {np.max(np.abs(output1[:-2] - output2[:-2]))}"
        })
    except Exception as e:
        results.append({
            "name": "Causal masking property",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Value scaling property
    # Scaling V by a constant should scale the output by the same constant
    try:
        np.random.seed(46)
        L, M, d = 5, 4, 3
        Q_prime = np.random.randn(L, M)
        K_prime = np.random.randn(L, M)
        V = np.random.randn(L, d)
        scale = 3.0
        
        output1 = fn(Q_prime, K_prime, V, is_bidirectional=False)
        output2 = fn(Q_prime, K_prime, scale * V, is_bidirectional=False)
        
        passed = np.allclose(scale * output1, output2, atol=1e-6, rtol=1e-6)
        results.append({
            "name": "Value scaling property (unidirectional)",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(scale * output1 - output2))}"
        })
    except Exception as e:
        results.append({
            "name": "Value scaling property (unidirectional)",
            "passed": False,
            "detail": str(e)
        })
    
    return results
