import numpy as np

def check(fn):
    results = []
    
    # Test 1: Permutation invariance - order of patches should not affect result
    try:
        np.random.seed(42)
        feature_dim = 4
        image_height, image_width = 10, 10
        
        # Create overlapping patches
        patch_features = [
            np.array([1.0, 2.0, 3.0, 4.0]),
            np.array([5.0, 6.0, 7.0, 8.0]),
            np.array([9.0, 10.0, 11.0, 12.0])
        ]
        patch_coords = [
            (0, 0, 5, 5),
            (3, 3, 8, 8),
            (5, 5, 10, 10)
        ]
        
        result1 = fn(patch_features, patch_coords, image_height, image_width, feature_dim)
        
        # Permute the order
        perm_indices = [2, 0, 1]
        patch_features_perm = [patch_features[i] for i in perm_indices]
        patch_coords_perm = [patch_coords[i] for i in perm_indices]
        
        result2 = fn(patch_features_perm, patch_coords_perm, image_height, image_width, feature_dim)
        
        passed = np.allclose(result1, result2, atol=1e-6)
        results.append({
            "name": "permutation_invariance",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result1 - result2))}" if not passed else "Permutation invariant"
        })
    except Exception as e:
        results.append({"name": "permutation_invariance", "passed": False, "detail": str(e)})
    
    # Test 2: Single patch covering entire image should equal that patch's features everywhere
    try:
        feature_dim = 3
        image_height, image_width = 8, 8
        
        patch_feature = np.array([2.5, -1.0, 3.7])
        patch_features = [patch_feature]
        patch_coords = [(0, 0, image_width, image_height)]
        
        result = fn(patch_features, patch_coords, image_height, image_width, feature_dim)
        
        # Every spatial location should have the same feature
        expected = np.zeros((1, feature_dim, image_height, image_width))
        expected[0, :, :, :] = patch_feature[:, np.newaxis, np.newaxis]
        
        passed = np.allclose(result, expected, atol=1e-6)
        results.append({
            "name": "single_full_patch",
            "passed": passed,
            "detail": f"Max diff: {np.max(np.abs(result - expected))}" if not passed else "Single patch correct"
        })
    except Exception as e:
        results.append({"name": "single_full_patch", "passed": False, "detail": str(e)})
    
    # Test 3: Non-overlapping patches should preserve individual features in their regions
    try:
        feature_dim = 2
        image_height, image_width = 10, 10
        
        patch_features = [
            np.array([1.0, 2.0]),
            np.array([3.0, 4.0]),
            np.array([5.0, 6.0]),
            np.array([7.0, 8.0])
        ]
        patch_coords = [
            (0, 0, 5, 5),    # top-left quadrant
            (5, 0, 10, 5),   # top-right quadrant
            (0, 5, 5, 10),   # bottom-left quadrant
            (5, 5, 10, 10)   # bottom-right quadrant
        ]
        
        result = fn(patch_features, patch_coords, image_height, image_width, feature_dim)
        
        # Check each quadrant has the correct feature
        passed = True
        for i, (left, upper, right, lower) in enumerate(patch_coords):
            region = result[0, :, upper:lower, left:right]
            expected_val = patch_features[i][:, np.newaxis, np.newaxis]
            if not np.allclose(region, expected_val, atol=1e-6):
                passed = False
                break
        
        results.append({
            "name": "non_overlapping_patches",
            "passed": passed,
            "detail": "Non-overlapping patches preserve features" if passed else "Feature mismatch in non-overlapping regions"
        })
    except Exception as e:
        results.append({"name": "non_overlapping_patches", "passed": False, "detail": str(e)})
    
    # Test 4: Overlapping identical patches should equal that patch's features
    try:
        feature_dim = 3
        image_height, image_width = 6, 6
        
        identical_feature = np.array([1.5, 2.5, 3.5])
        patch_features = [identical_feature.copy() for _ in range(4)]
        patch_coords = [
            (0, 0, 4, 4),
            (2, 2, 6, 6),
            (1, 1, 5, 5),
            (0, 2, 4, 6)
        ]
        
        result = fn(patch_features, patch_coords, image_height, image_width, feature_dim)
        
        # Find the union of all patches - should all have identical_feature
        covered_mask = np.zeros((image_height, image_width), dtype=bool)
        for left, upper, right, lower in patch_coords:
            covered_mask[upper:lower, left:right] = True
        
        # All covered locations should have the identical feature
        passed = True
        for h in range(image_height):
            for w in range(image_width):
                if covered_mask[h, w]:
                    if not np.allclose(result[0, :, h, w], identical_feature, atol=1e-6):
                        passed = False
                        break
            if not passed:
                break
        
        results.append({
            "name": "identical_overlapping_patches",
            "passed": passed,
            "detail": "Identical patches average to themselves" if passed else "Averaging identical patches failed"
        })
    except Exception as e:
        results.append({"name": "identical_overlapping_patches", "passed": False, "detail": str(e)})
    
    # Test 5: Output shape and dtype verification
    try:
        feature_dim = 5
        image_height, image_width = 12, 15
        
        patch_features = [np.random.randn(feature_dim) for _ in range(3)]
        patch_coords = [(0, 0, 5, 5), (5, 5, 10, 10), (10, 10, 15, 12)]
        
        result = fn(patch_features, patch_coords, image_height, image_width, feature_dim)
        
        shape_correct = result.shape == (1, feature_dim, image_height, image_width)
        dtype_correct = result.dtype == np.float64
        
        passed = shape_correct and dtype_correct
        results.append({
            "name": "output_shape_and_dtype",
            "passed": passed,
            "detail": f"Shape: {result.shape}, dtype: {result.dtype}" if not passed else "Shape and dtype correct"
        })
    except Exception as e:
        results.append({"name": "output_shape_and_dtype", "passed": False, "detail": str(e)})
    
    return results
