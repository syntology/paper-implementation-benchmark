import numpy as np

def check(fn):
    results = []
    
    # Test 1: Empty edges for all tasks should return 0
    # Mathematical property: If E_t = 0 for all tasks, the sum is empty, result is 0
    try:
        losses = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        edge_indices = [np.array([], dtype=np.int64).reshape(0, 2), 
                        np.array([], dtype=np.int64).reshape(0, 2)]
        result = fn(losses, edge_indices)
        passed = np.isclose(result, 0.0, atol=1e-6)
        results.append({
            "name": "empty_edges_all_tasks_returns_zero",
            "passed": passed,
            "detail": f"Expected 0.0, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "empty_edges_all_tasks_returns_zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Single edge with equal losses should contribute log(1) = 0
    # Mathematical property: If losses[i,t] == losses[j,t], then max(0, 0) = 0, exp(0) = 1
    # Contribution: log((1/1) * 1) = log(1) = 0
    try:
        losses = np.array([[5.0, 10.0], [5.0, 20.0]], dtype=np.float64)
        edge_indices = [np.array([[0, 1]], dtype=np.int64),
                        np.array([], dtype=np.int64).reshape(0, 2)]
        result = fn(losses, edge_indices)
        passed = np.isclose(result, 0.0, atol=1e-6)
        results.append({
            "name": "single_edge_equal_losses_returns_zero",
            "passed": passed,
            "detail": f"Expected 0.0, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "single_edge_equal_losses_returns_zero",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Result must be non-negative
    # Mathematical property: log of positive number is real; sum of logs is unbounded but each term >= log(exp(0)) = 0
    # Actually: each term is log((1/E_t) * sum of exp(...)) where exp(...) >= 1 (since max(0,x) >= 0)
    # So each term >= log(1/E_t) which can be negative. But overall property: result is well-defined real number
    # Better property: monotonicity in loss differences
    try:
        np.random.seed(42)
        losses = np.random.randn(5, 3).astype(np.float64)
        edge_indices = [
            np.array([[0, 1], [1, 2]], dtype=np.int64),
            np.array([[2, 3], [3, 4]], dtype=np.int64),
            np.array([[0, 4]], dtype=np.int64)
        ]
        result = fn(losses, edge_indices)
        passed = np.isfinite(result)
        results.append({
            "name": "result_is_finite",
            "passed": passed,
            "detail": f"Result {result} is finite: {passed}"
        })
    except Exception as e:
        results.append({
            "name": "result_is_finite",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Increasing loss differences should increase the result
    # Mathematical property: If we increase losses[i,t] - losses[j,t], the exp term increases, so log increases
    try:
        losses_1 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        losses_2 = np.array([[2.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        edge_indices = [np.array([[0, 1]], dtype=np.int64),
                        np.array([], dtype=np.int64).reshape(0, 2)]
        
        result_1 = fn(losses_1, edge_indices)
        result_2 = fn(losses_2, edge_indices)
        
        passed = result_2 > result_1
        results.append({
            "name": "monotonicity_in_loss_difference",
            "passed": passed,
            "detail": f"Result with larger difference {result_2} > {result_1}: {passed}"
        })
    except Exception as e:
        results.append({
            "name": "monotonicity_in_loss_difference",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Multiple identical edges should average correctly
    # Mathematical property: log((1/2) * (exp(d) + exp(d))) = log(exp(d)) = d (where d = max(0, diff))
    try:
        losses = np.array([[2.0], [0.0]], dtype=np.float64)
        edge_indices = [np.array([[0, 1], [0, 1]], dtype=np.int64)]
        result = fn(losses, edge_indices)
        expected = np.log(2.0)  # log((1/2) * (exp(2) + exp(2))) = log(exp(2)) = 2
        passed = np.isclose(result, 2.0, atol=1e-6)
        results.append({
            "name": "multiple_identical_edges_averaging",
            "passed": passed,
            "detail": f"Expected 2.0, got {result}"
        })
    except Exception as e:
        results.append({
            "name": "multiple_identical_edges_averaging",
            "passed": False,
            "detail": str(e)
        })
    
    return results
