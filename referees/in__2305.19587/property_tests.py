import numpy as np

def check(fn):
    results = []
    
    # Test 1: Uniform weights should give arithmetic mean
    try:
        B, D = 5, 10
        np.random.seed(42)
        task_gradients = np.random.randn(B, D)
        task_weights = np.ones(B) / B
        result = fn(task_gradients, task_weights)
        expected = np.mean(task_gradients, axis=0)
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "uniform weights produce arithmetic mean"
        results.append({"name": "uniform_weights_arithmetic_mean", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "uniform_weights_arithmetic_mean", "passed": False, "detail": str(e)})
    
    # Test 2: Single task with weight 1.0 should return that task's gradient
    try:
        B, D = 1, 8
        np.random.seed(43)
        task_gradients = np.random.randn(B, D)
        task_weights = np.array([1.0])
        result = fn(task_gradients, task_weights)
        expected = task_gradients[0]
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "single task returns its gradient"
        results.append({"name": "single_task_identity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "single_task_identity", "passed": False, "detail": str(e)})
    
    # Test 3: Zero weights should give zero gradient
    try:
        B, D = 4, 6
        np.random.seed(44)
        task_gradients = np.random.randn(B, D)
        task_weights = np.zeros(B)
        result = fn(task_gradients, task_weights)
        expected = np.zeros(D)
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_abs={np.max(np.abs(result))}" if not passed else "zero weights produce zero gradient"
        results.append({"name": "zero_weights_zero_output", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "zero_weights_zero_output", "passed": False, "detail": str(e)})
    
    # Test 4: Scaling all weights by constant c scales output by c
    try:
        B, D = 6, 12
        np.random.seed(45)
        task_gradients = np.random.randn(B, D)
        task_weights = np.random.rand(B)
        c = 2.5
        result1 = fn(task_gradients, task_weights)
        result2 = fn(task_gradients, c * task_weights)
        expected = c * result1
        passed = np.allclose(result2, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result2 - expected))}" if not passed else "weight scaling is linear"
        results.append({"name": "weight_scaling_linearity", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "weight_scaling_linearity", "passed": False, "detail": str(e)})
    
    # Test 5: One-hot weight vector selects corresponding task gradient
    try:
        B, D = 7, 9
        np.random.seed(46)
        task_gradients = np.random.randn(B, D)
        selected_task = 3
        task_weights = np.zeros(B)
        task_weights[selected_task] = 1.0
        result = fn(task_gradients, task_weights)
        expected = task_gradients[selected_task]
        passed = np.allclose(result, expected, atol=1e-6)
        detail = f"max_diff={np.max(np.abs(result - expected))}" if not passed else "one-hot weight selects task"
        results.append({"name": "one_hot_weight_selection", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "one_hot_weight_selection", "passed": False, "detail": str(e)})
    
    return results
