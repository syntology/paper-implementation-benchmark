import numpy as np

def check(fn):
    results = []
    
    # Test 1: Output length and inclusion of selected_idx
    try:
        features = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
        selected_idx = 1
        L = 3
        output = fn(features, selected_idx, L)
        
        # Check output is 1D array of correct length
        assert output.ndim == 1, f"Output should be 1D, got {output.ndim}D"
        assert len(output) == L, f"Output length should be {L}, got {len(output)}"
        
        # Check selected_idx is in output
        assert selected_idx in output, f"selected_idx {selected_idx} not in output {output}"
        
        # Check all indices are valid
        assert np.all(output >= 0) and np.all(output < len(features)), \
            f"Output indices out of bounds: {output}"
        
        # Check no duplicates
        assert len(np.unique(output)) == L, f"Output contains duplicates: {output}"
        
        results.append({"name": "output_length_and_selected_idx_inclusion", "passed": True, "detail": ""})
    except Exception as e:
        results.append({"name": "output_length_and_selected_idx_inclusion", "passed": False, "detail": str(e)})
    
    # Test 2: Output is sorted by distance (with ties broken by index)
    try:
        features = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 0.0], [2.0, 0.0], [0.25, 0.0]])
        selected_idx = 0
        L = 4
        output = fn(features, selected_idx, L)
        
        # Compute distances manually
        center = features[selected_idx]
        distances = np.linalg.norm(features - center, axis=1)
        
        # Get expected sorted order (by distance, then by index for ties)
        expected_order = np.argsort(distances, kind='stable')[:L]
        
        # Check output matches expected order
        assert np.array_equal(output, expected_order), \
            f"Output {output} doesn't match expected order {expected_order}"
        
        # Verify distances are non-decreasing
        output_distances = distances[output]
        assert np.all(output_distances[:-1] <= output_distances[1:] + 1e-6), \
            f"Distances not sorted: {output_distances}"
        
        results.append({"name": "output_sorted_by_distance", "passed": True, "detail": ""})
    except Exception as e:
        results.append({"name": "output_sorted_by_distance", "passed": False, "detail": str(e)})
    
    # Test 3: Translation invariance
    try:
        features = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        selected_idx = 0
        L = 2
        output1 = fn(features, selected_idx, L)
        
        # Translate all features by a constant vector
        translation = np.array([10.0, -5.0])
        features_translated = features + translation
        output2 = fn(features_translated, selected_idx, L)
        
        # Relative distances should be preserved, so output order should be identical
        assert np.array_equal(output1, output2), \
            f"Translation changed output: {output1} vs {output2}"
        
        results.append({"name": "translation_invariance", "passed": True, "detail": ""})
    except Exception as e:
        results.append({"name": "translation_invariance", "passed": False, "detail": str(e)})
    
    # Test 4: Uniform scaling invariance (relative ordering preserved)
    try:
        features = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
        selected_idx = 0
        L = 3
        output1 = fn(features, selected_idx, L)
        
        # Scale all features by a positive constant
        scale = 5.0
        features_scaled = features * scale
        output2 = fn(features_scaled, selected_idx, L)
        
        # Relative ordering should be preserved under uniform scaling
        assert np.array_equal(output1, output2), \
            f"Uniform scaling changed output: {output1} vs {output2}"
        
        results.append({"name": "uniform_scaling_invariance", "passed": True, "detail": ""})
    except Exception as e:
        results.append({"name": "uniform_scaling_invariance", "passed": False, "detail": str(e)})
    
    # Test 5: L >= N returns all indices sorted by distance
    try:
        features = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 0.0]])
        selected_idx = 0
        N = len(features)
        L = N + 5  # Request more than available
        output = fn(features, selected_idx, L)
        
        # Should return all N indices
        assert len(output) == N, f"Expected {N} indices, got {len(output)}"
        
        # Should contain all indices
        assert set(output) == set(range(N)), f"Output doesn't contain all indices: {output}"
        
        # Should be sorted by distance
        center = features[selected_idx]
        distances = np.linalg.norm(features - center, axis=1)
        output_distances = distances[output]
        assert np.all(output_distances[:-1] <= output_distances[1:] + 1e-6), \
            f"Distances not sorted: {output_distances}"
        
        results.append({"name": "L_greater_than_N_returns_all", "passed": True, "detail": ""})
    except Exception as e:
        results.append({"name": "L_greater_than_N_returns_all", "passed": False, "detail": str(e)})
    
    return results
