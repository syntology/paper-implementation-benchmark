import numpy as np

def check(fn):
    results = []
    np.random.seed(42)
    
    # Test 1: Output shape is always (batch_size, num_filters)
    def test_output_shape():
        try:
            batch_size, input_dim, num_filters = 5, 3, 4
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            
            # Test with various filter_indices
            for filter_indices in [[], [0], [1, 3], [0, 1, 2, 3]]:
                output = fn(z_in, theta, filter_indices)
                if output.shape != (batch_size, num_filters):
                    return False, f"Expected shape {(batch_size, num_filters)}, got {output.shape}"
            
            return True, "Output shape always correct"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_output_shape()
    results.append({"name": "output_shape_invariant", "passed": passed, "detail": detail})
    
    # Test 2: Empty filter_indices returns all zeros
    def test_empty_filter_indices():
        try:
            batch_size, input_dim, num_filters = 3, 4, 5
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            
            output = fn(z_in, theta, [])
            expected = np.zeros((batch_size, num_filters))
            
            if not np.allclose(output, expected, atol=1e-6):
                return False, f"Empty filter_indices should return zeros, got {output}"
            
            return True, "Empty filter_indices returns zeros"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_empty_filter_indices()
    results.append({"name": "empty_filter_indices_zeros", "passed": passed, "detail": detail})
    
    # Test 3: Output is non-negative (ReLU property)
    def test_non_negativity():
        try:
            batch_size, input_dim, num_filters = 4, 5, 6
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            filter_indices = [0, 2, 4]
            
            output = fn(z_in, theta, filter_indices)
            
            if np.any(output < -1e-6):
                return False, f"Output contains negative values: min={np.min(output)}"
            
            return True, "All outputs non-negative (ReLU property)"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_non_negativity()
    results.append({"name": "non_negativity_relu", "passed": passed, "detail": detail})
    
    # Test 4: Selected filters have identical values across their positions
    def test_selected_filters_identical():
        try:
            batch_size, input_dim, num_filters = 3, 4, 5
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            filter_indices = [1, 3]
            
            output = fn(z_in, theta, filter_indices)
            
            # All selected filter columns should be identical
            for i in range(batch_size):
                for j in filter_indices:
                    if not np.allclose(output[i, j], output[i, filter_indices[0]], atol=1e-6):
                        return False, f"Selected filters should have identical values at batch {i}"
            
            return True, "Selected filters have identical values"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_selected_filters_identical()
    results.append({"name": "selected_filters_identical", "passed": passed, "detail": detail})
    
    # Test 5: Unselected filters are zero
    def test_unselected_filters_zero():
        try:
            batch_size, input_dim, num_filters = 3, 4, 5
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            filter_indices = [0, 2]
            
            output = fn(z_in, theta, filter_indices)
            
            # Unselected filters should be zero
            unselected = [i for i in range(num_filters) if i not in filter_indices]
            for j in unselected:
                if not np.allclose(output[:, j], 0, atol=1e-6):
                    return False, f"Unselected filter {j} should be zero, got {output[:, j]}"
            
            return True, "Unselected filters are zero"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_unselected_filters_zero()
    results.append({"name": "unselected_filters_zero", "passed": passed, "detail": detail})
    
    # Test 6: Single filter selection equals ReLU of that filter
    def test_single_filter_selection():
        try:
            batch_size, input_dim, num_filters = 3, 4, 5
            z_in = np.random.randn(batch_size, input_dim)
            theta = np.random.randn(num_filters, input_dim)
            selected_idx = 2
            
            output = fn(z_in, theta, [selected_idx])
            
            # Compute expected: ReLU(theta[selected_idx] @ z_in.T)
            expected_values = np.maximum(0, theta[selected_idx] @ z_in.T)
            
            # Check selected filter column
            if not np.allclose(output[:, selected_idx], expected_values, atol=1e-6):
                return False, f"Single filter output mismatch"
            
            # Check other columns are zero
            for j in range(num_filters):
                if j != selected_idx:
                    if not np.allclose(output[:, j], 0, atol=1e-6):
                        return False, f"Non-selected filter {j} should be zero"
            
            return True, "Single filter selection matches ReLU"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_single_filter_selection()
    results.append({"name": "single_filter_relu_match", "passed": passed, "detail": detail})
    
    return results
