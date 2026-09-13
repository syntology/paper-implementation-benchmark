import numpy as np

def check(fn):
    results = []
    
    # Test 1: Homogeneity - scaling depth by constant k should scale output by k
    # (in the direction of the ray from camera origin)
    try:
        np.random.seed(42)
        point_2d = np.array([320.0, 240.0])
        depth1 = 1.0
        P = np.eye(4)
        P[0, 0] = 500.0  # focal length x
        P[1, 1] = 500.0  # focal length y
        P[0, 2] = 320.0  # principal point x
        P[1, 2] = 240.0  # principal point y
        T = np.eye(4)
        
        result1 = fn(point_2d, depth1, P, T)
        result2 = fn(point_2d, 2.0 * depth1, P, T)
        
        # Results should be collinear with origin; result2 ≈ 2 * result1
        ratio = result2 / (result1 + 1e-10)
        expected_ratio = 2.0
        passed = np.allclose(ratio, expected_ratio, atol=1e-5)
        results.append({
            "name": "Depth scaling homogeneity",
            "passed": passed,
            "detail": f"Scaling depth by 2: ratio={ratio}, expected≈{expected_ratio}"
        })
    except Exception as e:
        results.append({
            "name": "Depth scaling homogeneity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Identity transformation - with identity projection and transform,
    # unprojection should recover scaled 2D point in 3D
    try:
        np.random.seed(43)
        point_2d = np.array([100.0, 50.0])
        depth = 5.0
        P = np.eye(4)
        T = np.eye(4)
        
        result = fn(point_2d, depth, P, T)
        
        # With identity matrices, result should be [u*depth, v*depth, depth]
        expected = np.array([point_2d[0] * depth, point_2d[1] * depth, depth])
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "Identity transformation recovery",
            "passed": passed,
            "detail": f"Result: {result}, Expected: {expected}"
        })
    except Exception as e:
        results.append({
            "name": "Identity transformation recovery",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Inverse consistency - applying transformation then inverse should recover original
    # (testing that M_inv is correctly computed)
    try:
        np.random.seed(44)
        point_2d = np.array([256.0, 512.0])
        depth = 3.5
        
        # Create a well-conditioned projection matrix
        P = np.array([
            [500.0, 0.0, 320.0, 0.0],
            [0.0, 500.0, 240.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        
        # Create a well-conditioned transform (small rotation + translation)
        T = np.eye(4)
        T[0, 3] = 0.1
        T[1, 3] = 0.05
        
        result = fn(point_2d, depth, P, T)
        
        # Result should be a valid 3D point (finite, not NaN)
        passed = np.all(np.isfinite(result)) and result.shape == (3,)
        results.append({
            "name": "Inverse matrix consistency",
            "passed": passed,
            "detail": f"Result is finite 3D point: {result}"
        })
    except Exception as e:
        results.append({
            "name": "Inverse matrix consistency",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Output shape and type - result must always be length-3 array
    try:
        np.random.seed(45)
        point_2d = np.array([100.0, 200.0])
        depth = 2.0
        P = np.eye(4)
        P[0, 0] = 600.0
        P[1, 1] = 600.0
        P[0, 2] = 320.0
        P[1, 2] = 240.0
        T = np.eye(4)
        
        result = fn(point_2d, depth, P, T)
        
        passed = isinstance(result, np.ndarray) and result.shape == (3,) and result.dtype in [np.float32, np.float64]
        results.append({
            "name": "Output shape and type",
            "passed": passed,
            "detail": f"Shape: {result.shape}, dtype: {result.dtype}"
        })
    except Exception as e:
        results.append({
            "name": "Output shape and type",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Determinism - same inputs produce same outputs
    try:
        np.random.seed(46)
        point_2d = np.array([150.0, 300.0])
        depth = 4.2
        P = np.array([
            [480.0, 0.0, 320.0, 0.0],
            [0.0, 480.0, 240.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        T = np.eye(4)
        T[2, 3] = 0.2
        
        result1 = fn(point_2d.copy(), depth, P.copy(), T.copy())
        result2 = fn(point_2d.copy(), depth, P.copy(), T.copy())
        
        passed = np.allclose(result1, result2, atol=1e-10)
        results.append({
            "name": "Determinism",
            "passed": passed,
            "detail": f"Result1: {result1}, Result2: {result2}"
        })
    except Exception as e:
        results.append({
            "name": "Determinism",
            "passed": False,
            "detail": str(e)
        })
    
    return results
