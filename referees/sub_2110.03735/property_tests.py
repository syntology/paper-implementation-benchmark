import numpy as np

def check(fn):
    results = []
    
    # Test 1: Norm preservation - if input norm <= c_delta, output equals input
    try:
        delta = np.array([3.0, 4.0])
        c_delta = 10.0
        result = fn(delta, c_delta)
        passed = np.allclose(result, delta, atol=1e-6)
        detail = f"Input norm {np.linalg.norm(delta):.6f} <= c_delta {c_delta}, expected unchanged, got norm {np.linalg.norm(result):.6f}"
        results.append({"name": "norm_preservation_within_ball", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "norm_preservation_within_ball", "passed": False, "detail": str(e)})
    
    # Test 2: Projection to boundary - if input norm > c_delta, output norm equals c_delta
    try:
        delta = np.array([6.0, 8.0])  # norm = 10
        c_delta = 5.0
        result = fn(delta, c_delta)
        result_norm = np.linalg.norm(result)
        passed = np.allclose(result_norm, c_delta, atol=1e-6)
        detail = f"Input norm {np.linalg.norm(delta):.6f} > c_delta {c_delta}, output norm {result_norm:.6f}, expected {c_delta}"
        results.append({"name": "projection_to_boundary", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "projection_to_boundary", "passed": False, "detail": str(e)})
    
    # Test 3: Direction preservation - projection preserves direction (output parallel to input)
    try:
        delta = np.array([3.0, 4.0, 12.0])  # norm = 13
        c_delta = 6.5
        result = fn(delta, c_delta)
        # Check if result is parallel to delta by verifying result = k * delta for some scalar k
        if np.linalg.norm(delta) > 1e-9:
            k = result[0] / delta[0] if abs(delta[0]) > 1e-9 else result[1] / delta[1]
            expected = k * delta
            passed = np.allclose(result, expected, atol=1e-6)
            detail = f"Direction preserved: result/delta ratio consistent across dimensions"
        else:
            passed = False
            detail = "Degenerate case"
        results.append({"name": "direction_preservation", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "direction_preservation", "passed": False, "detail": str(e)})
    
    # Test 4: Scaling invariance - scaling both delta and c_delta by same factor preserves result up to that factor
    try:
        delta = np.array([1.0, 2.0, 2.0])  # norm = 3
        c_delta = 2.0
        scale = 5.0
        result1 = fn(delta, c_delta)
        result2 = fn(scale * delta, scale * c_delta)
        passed = np.allclose(result2, scale * result1, atol=1e-6)
        detail = f"Scaling both delta and c_delta by {scale} preserves scaled result"
        results.append({"name": "scaling_invariance", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: Idempotence - projecting twice gives same result as projecting once
    try:
        delta = np.array([9.0, 12.0])  # norm = 15
        c_delta = 7.5
        result1 = fn(delta, c_delta)
        result2 = fn(result1, c_delta)
        passed = np.allclose(result1, result2, atol=1e-6)
        detail = f"Projecting twice gives same result: norm1={np.linalg.norm(result1):.6f}, norm2={np.linalg.norm(result2):.6f}"
        results.append({"name": "idempotence", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "idempotence", "passed": False, "detail": str(e)})
    
    return results
