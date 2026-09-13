import numpy as np

def check(fn):
    results = []
    
    # Test 1: When theta is inside the ball, return theta unchanged
    try:
        theta_star = np.array([0.0, 0.0, 0.0])
        delta = 5.0
        theta = np.array([1.0, 2.0, 2.0])  # distance = 3.0 < 5.0
        result = fn(theta, theta_star, delta)
        passed = np.allclose(result, theta, atol=1e-6)
        detail = f"Expected {theta}, got {result}" if not passed else "Correctly returned unchanged theta"
        results.append({"name": "inside_ball_unchanged", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "inside_ball_unchanged", "passed": False, "detail": str(e)})
    
    # Test 2: When theta is on the boundary, return theta unchanged
    try:
        theta_star = np.array([0.0, 0.0])
        delta = 5.0
        theta = np.array([3.0, 4.0])  # distance = 5.0 == delta
        result = fn(theta, theta_star, delta)
        passed = np.allclose(result, theta, atol=1e-6)
        detail = f"Expected {theta}, got {result}" if not passed else "Correctly returned unchanged theta on boundary"
        results.append({"name": "on_boundary_unchanged", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "on_boundary_unchanged", "passed": False, "detail": str(e)})
    
    # Test 3: When theta is outside the ball, projected point is at distance delta from theta_star
    try:
        theta_star = np.array([0.0, 0.0, 0.0])
        delta = 2.0
        theta = np.array([3.0, 4.0, 0.0])  # distance = 5.0 > 2.0
        result = fn(theta, theta_star, delta)
        dist_to_center = np.linalg.norm(result - theta_star)
        passed = np.isclose(dist_to_center, delta, atol=1e-6)
        detail = f"Expected distance {delta}, got {dist_to_center}" if not passed else "Correctly projected to boundary"
        results.append({"name": "outside_projects_to_boundary", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "outside_projects_to_boundary", "passed": False, "detail": str(e)})
    
    # Test 4: Projection preserves direction from theta_star to theta
    try:
        theta_star = np.array([1.0, 2.0, 3.0])
        delta = 1.5
        theta = np.array([5.0, 6.0, 7.0])  # distance = sqrt(48) > 1.5
        result = fn(theta, theta_star, delta)
        direction_original = theta - theta_star
        direction_result = result - theta_star
        # Directions should be parallel (one is scalar multiple of other)
        cross_product = np.linalg.norm(np.cross(direction_original, direction_result))
        passed = np.isclose(cross_product, 0.0, atol=1e-6)
        detail = f"Cross product: {cross_product}" if not passed else "Direction preserved"
        results.append({"name": "direction_preserved", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "direction_preserved", "passed": False, "detail": str(e)})
    
    # Test 5: Output shape matches input shape
    try:
        for d in [1, 5, 10]:
            theta_star = np.zeros(d)
            delta = 1.0
            theta = np.ones(d) * 0.5
            result = fn(theta, theta_star, delta)
            passed = result.shape == (d,) and isinstance(result, np.ndarray)
            if not passed:
                raise ValueError(f"Expected shape ({d},), got {result.shape}")
        results.append({"name": "output_shape_matches_input", "passed": True, "detail": "All dimensions preserved"})
    except Exception as e:
        results.append({"name": "output_shape_matches_input", "passed": False, "detail": str(e)})
    
    return results
