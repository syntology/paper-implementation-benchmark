import numpy as np

def check(fn):
    results = []
    
    # Test 1: Single-point cluster has typicality of 0
    # When a cluster contains only the query point, the centroid equals the point,
    # so distance is 0 and typicality (negative distance) is 0.
    try:
        embeddings = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
        cluster_assignments = np.array([0, 1], dtype=np.int32)
        point_index = 0
        result = fn(embeddings, cluster_assignments, point_index)
        passed = np.isclose(result, 0.0, atol=1e-6)
        results.append({
            "name": "single_point_cluster_typicality_zero",
            "passed": passed,
            "detail": f"Expected 0.0, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "single_point_cluster_typicality_zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Typicality is always non-positive (negative distance)
    # By definition, typicality = -distance, and distance >= 0, so typicality <= 0.
    try:
        np.random.seed(42)
        embeddings = np.random.randn(10, 5).astype(np.float64)
        cluster_assignments = np.random.randint(0, 3, size=10)
        for point_index in range(10):
            result = fn(embeddings, cluster_assignments, point_index)
            passed = result <= 1e-6  # Allow small numerical tolerance
            if not passed:
                raise ValueError(f"Typicality {result} is positive at index {point_index}")
        results.append({
            "name": "typicality_non_positive",
            "passed": True,
            "detail": "All typicality scores are non-positive"
        })
    except Exception as e:
        results.append({
            "name": "typicality_non_positive",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Identical points in cluster have same typicality
    # If two points are identical and in the same cluster, they should have
    # the same distance to the centroid, hence same typicality.
    try:
        point = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        embeddings = np.vstack([point, point, np.array([4.0, 5.0, 6.0])])
        cluster_assignments = np.array([0, 0, 0], dtype=np.int32)
        result_0 = fn(embeddings, cluster_assignments, 0)
        result_1 = fn(embeddings, cluster_assignments, 1)
        passed = np.isclose(result_0, result_1, atol=1e-6)
        results.append({
            "name": "identical_points_same_typicality",
            "passed": passed,
            "detail": f"Point 0 typicality: {result_0}, Point 1 typicality: {result_1}"
        })
    except Exception as e:
        results.append({
            "name": "identical_points_same_typicality",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Centroid of two symmetric points lies between them
    # For a cluster with two points equidistant from origin, the centroid is their mean.
    # A point at the centroid should have typicality 0.
    try:
        p1 = np.array([1.0, 0.0], dtype=np.float64)
        p2 = np.array([-1.0, 0.0], dtype=np.float64)
        centroid = (p1 + p2) / 2.0  # [0, 0]
        embeddings = np.vstack([p1, p2, centroid])
        cluster_assignments = np.array([0, 0, 0], dtype=np.int32)
        result = fn(embeddings, cluster_assignments, 2)
        passed = np.isclose(result, 0.0, atol=1e-6)
        results.append({
            "name": "point_at_centroid_zero_typicality",
            "passed": passed,
            "detail": f"Expected 0.0, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "point_at_centroid_zero_typicality",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Typicality respects Euclidean distance definition
    # Manually compute expected typicality and verify against implementation.
    try:
        embeddings = np.array([
            [0.0, 0.0],
            [3.0, 4.0],
            [6.0, 8.0]
        ], dtype=np.float64)
        cluster_assignments = np.array([0, 0, 0], dtype=np.int32)
        point_index = 1
        
        # Centroid = mean of all three points
        centroid = np.mean(embeddings, axis=0)  # [3, 4]
        # Distance from point 1 to centroid
        expected_distance = np.linalg.norm(embeddings[point_index] - centroid)
        expected_typicality = -expected_distance
        
        result = fn(embeddings, cluster_assignments, point_index)
        passed = np.isclose(result, expected_typicality, atol=1e-6)
        results.append({
            "name": "euclidean_distance_correctness",
            "passed": passed,
            "detail": f"Expected {expected_typicality}, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "euclidean_distance_correctness",
            "passed": False,
            "detail": str(e)
        })
    
    return results
