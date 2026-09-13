import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output sums to 1.0 (probability distribution property)
    try:
        k = 3
        K = np.array([
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.4],
            [0.3, 0.4, 1.0]
        ])
        lambda_reg = 0.1
        
        alpha_pretrain = fn(K, lambda_reg, 'pretrain')
        alpha_finetune = fn(K, lambda_reg, 'finetune')
        
        sum_pretrain = np.sum(alpha_pretrain)
        sum_finetune = np.sum(alpha_finetune)
        
        passed = (np.abs(sum_pretrain - 1.0) < 1e-6 and 
                  np.abs(sum_finetune - 1.0) < 1e-6)
        detail = f"pretrain sum={sum_pretrain}, finetune sum={sum_finetune}"
        results.append({"name": "output_sums_to_one", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_sums_to_one", "passed": False, "detail": str(e)})
    
    # Test 2: Output is non-negative (probability property)
    try:
        k = 4
        np.random.seed(42)
        K = np.random.rand(k, k)
        K = (K + K.T) / 2  # Make symmetric
        K = K + np.eye(k)  # Ensure positive definite
        lambda_reg = 0.1
        
        alpha_pretrain = fn(K, lambda_reg, 'pretrain')
        alpha_finetune = fn(K, lambda_reg, 'finetune')
        
        passed = (np.all(alpha_pretrain >= -1e-6) and 
                  np.all(alpha_finetune >= -1e-6))
        detail = f"pretrain min={np.min(alpha_pretrain)}, finetune min={np.min(alpha_finetune)}"
        results.append({"name": "output_non_negative", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_non_negative", "passed": False, "detail": str(e)})
    
    # Test 3: Output shape is (k,) and dtype is float64
    try:
        k = 5
        K = np.eye(k)
        lambda_reg = 0.1
        
        alpha_pretrain = fn(K, lambda_reg, 'pretrain')
        alpha_finetune = fn(K, lambda_reg, 'finetune')
        
        passed = (alpha_pretrain.shape == (k,) and 
                  alpha_finetune.shape == (k,) and
                  alpha_pretrain.dtype == np.float64 and
                  alpha_finetune.dtype == np.float64)
        detail = f"pretrain shape={alpha_pretrain.shape} dtype={alpha_pretrain.dtype}, finetune shape={alpha_finetune.shape} dtype={alpha_finetune.dtype}"
        results.append({"name": "output_shape_and_dtype", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_and_dtype", "passed": False, "detail": str(e)})
    
    # Test 4: Identity matrix (degenerate case) - all weights equal
    try:
        k = 3
        K = np.eye(k)
        lambda_reg = 0.1
        
        alpha_pretrain = fn(K, lambda_reg, 'pretrain')
        alpha_finetune = fn(K, lambda_reg, 'finetune')
        
        expected = 1.0 / k
        passed = (np.allclose(alpha_pretrain, expected, atol=1e-6) and
                  np.allclose(alpha_finetune, expected, atol=1e-6))
        detail = f"pretrain={alpha_pretrain}, finetune={alpha_finetune}, expected={expected}"
        results.append({"name": "identity_matrix_uniform", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identity_matrix_uniform", "passed": False, "detail": str(e)})
    
    # Test 5: Mode difference - pretrain and finetune produce different results (inverse vs direct KRLS)
    try:
        k = 3
        K = np.array([
            [2.0, 0.5, 0.2],
            [0.5, 1.5, 0.3],
            [0.2, 0.3, 1.0]
        ])
        lambda_reg = 0.1
        
        alpha_pretrain = fn(K, lambda_reg, 'pretrain')
        alpha_finetune = fn(K, lambda_reg, 'finetune')
        
        # They should generally differ (unless by coincidence they're identical)
        # We check they're not identical within numerical tolerance
        passed = not np.allclose(alpha_pretrain, alpha_finetune, atol=1e-6)
        detail = f"pretrain={alpha_pretrain}, finetune={alpha_finetune}"
        results.append({"name": "mode_produces_different_results", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "mode_produces_different_results", "passed": False, "detail": str(e)})
    
    return results
