import numpy as np

def check(fn):
    results = []
    
    # Test 1: Identity kernel case - when K_train_train is identity,
    # predictions should equal Y_train reordered by K_test_train
    try:
        n_train = 3
        n_test = 2
        Y_train = np.array([1.0, 2.0, 3.0])
        K_train_train = np.eye(n_train)
        K_test_train = np.array([[1.0, 0.0, 0.0],
                                 [0.0, 1.0, 0.0]])
        
        pred = fn(K_test_train, K_train_train, Y_train)
        expected = np.array([1.0, 2.0])
        
        passed = np.allclose(pred, expected, atol=1e-6)
        detail = f"Expected {expected}, got {pred}" if not passed else "Identity kernel case passed"
        results.append({"name": "identity_kernel", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "identity_kernel", "passed": False, "detail": str(e)})
    
    # Test 2: Scaling invariance - scaling Y_train by constant c
    # should scale predictions by c
    try:
        np.random.seed(42)
        n_train = 4
        n_test = 3
        K_train_train = np.random.randn(n_train, n_train)
        K_train_train = K_train_train @ K_train_train.T + np.eye(n_train)
        K_test_train = np.random.randn(n_test, n_train)
        Y_train = np.random.randn(n_train)
        
        pred1 = fn(K_test_train, K_train_train, Y_train)
        
        scale = 2.5
        pred2 = fn(K_test_train, K_train_train, scale * Y_train)
        
        passed = np.allclose(pred2, scale * pred1, atol=1e-6)
        detail = f"Scaling by {scale}: max relative error {np.max(np.abs(pred2 - scale * pred1) / (np.abs(scale * pred1) + 1e-10))}" if not passed else "Scaling invariance passed"
        results.append({"name": "scaling_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 3: Single test point with single training point
    # f(x_test) = K[test, train] * K[train, train]^{-1} * y_train
    # = K[test, train] / K[train, train] * y_train
    try:
        K_test_train = np.array([[2.0]])
        K_train_train = np.array([[4.0]])
        Y_train = np.array([8.0])
        
        pred = fn(K_test_train, K_train_train, Y_train)
        expected = np.array([2.0 / 4.0 * 8.0])
        
        passed = np.allclose(pred, expected, atol=1e-6)
        detail = f"Expected {expected}, got {pred}" if not passed else "Single point case passed"
        results.append({"name": "single_point_case", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "single_point_case", "passed": False, "detail": str(e)})
    
    # Test 4: Zero labels - predictions should be zero
    try:
        np.random.seed(43)
        n_train = 5
        n_test = 4
        K_train_train = np.random.randn(n_train, n_train)
        K_train_train = K_train_train @ K_train_train.T + np.eye(n_train)
        K_test_train = np.random.randn(n_test, n_train)
        Y_train = np.zeros(n_train)
        
        pred = fn(K_test_train, K_train_train, Y_train)
        expected = np.zeros(n_test)
        
        passed = np.allclose(pred, expected, atol=1e-6)
        detail = f"Max prediction magnitude: {np.max(np.abs(pred))}" if not passed else "Zero labels case passed"
        results.append({"name": "zero_labels", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_labels", "passed": False, "detail": str(e)})
    
    # Test 5: Output shape and type correctness
    try:
        np.random.seed(44)
        n_train = 6
        n_test = 7
        K_train_train = np.random.randn(n_train, n_train)
        K_train_train = K_train_train @ K_train_train.T + np.eye(n_train)
        K_test_train = np.random.randn(n_test, n_train)
        Y_train = np.random.randn(n_train)
        
        pred = fn(K_test_train, K_train_train, Y_train)
        
        passed = (isinstance(pred, np.ndarray) and 
                 pred.shape == (n_test,) and 
                 pred.dtype in [np.float32, np.float64])
        detail = f"Shape: {pred.shape}, dtype: {pred.dtype}" if not passed else "Output shape and type correct"
        results.append({"name": "output_shape_type", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "output_shape_type", "passed": False, "detail": str(e)})
    
    return results
