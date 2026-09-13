import numpy as np

def check(fn):
    results = []
    
    # Test 1: Linearity in validation loss gradient
    # If val_loss_grad_theta is scaled by a constant c, the output should scale by -c
    try:
        np.random.seed(42)
        D, N = 5, 3
        val_loss_grad_theta = np.random.randn(D)
        train_loss_hessian_theta = np.random.randn(D, D)
        train_loss_hessian_theta = train_loss_hessian_theta @ train_loss_hessian_theta.T  # Make SPD
        train_loss_grad_theta_grad_w = np.random.randn(D, N)
        
        result1 = fn(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        c = 2.5
        result2 = fn(c * val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        expected = c * result1
        error = np.linalg.norm(result2 - expected)
        passed = error < 1e-6
        results.append({
            "name": "Linearity in validation gradient",
            "passed": passed,
            "detail": f"Scaling factor {c}: error = {error}"
        })
    except Exception as e:
        results.append({
            "name": "Linearity in validation gradient",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Linearity in mixed partial derivatives
    # If train_loss_grad_theta_grad_w is scaled by c, output should scale by -c
    try:
        np.random.seed(43)
        D, N = 5, 3
        val_loss_grad_theta = np.random.randn(D)
        train_loss_hessian_theta = np.random.randn(D, D)
        train_loss_hessian_theta = train_loss_hessian_theta @ train_loss_hessian_theta.T
        train_loss_grad_theta_grad_w = np.random.randn(D, N)
        
        result1 = fn(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        c = 3.7
        result2 = fn(val_loss_grad_theta, train_loss_hessian_theta, c * train_loss_grad_theta_grad_w)
        
        expected = c * result1
        error = np.linalg.norm(result2 - expected)
        passed = error < 1e-6
        results.append({
            "name": "Linearity in mixed partials",
            "passed": passed,
            "detail": f"Scaling factor {c}: error = {error}"
        })
    except Exception as e:
        results.append({
            "name": "Linearity in mixed partials",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Output shape and type
    # Output must be 1D numpy array of shape (N,)
    try:
        np.random.seed(44)
        D, N = 6, 4
        val_loss_grad_theta = np.random.randn(D)
        train_loss_hessian_theta = np.random.randn(D, D)
        train_loss_hessian_theta = train_loss_hessian_theta @ train_loss_hessian_theta.T
        train_loss_grad_theta_grad_w = np.random.randn(D, N)
        
        result = fn(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        passed = (isinstance(result, np.ndarray) and 
                  result.ndim == 1 and 
                  result.shape[0] == N and
                  result.dtype in [np.float32, np.float64])
        results.append({
            "name": "Output shape and type",
            "passed": passed,
            "detail": f"Shape: {result.shape}, dtype: {result.dtype}, ndim: {result.ndim}"
        })
    except Exception as e:
        results.append({
            "name": "Output shape and type",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Degenerate case - identity Hessian with orthogonal vectors
    # When H = I and val_loss_grad_theta ⊥ each column of train_loss_grad_theta_grad_w,
    # the result should be zero (or very close)
    try:
        np.random.seed(45)
        D, N = 4, 3
        # Create orthogonal vectors
        val_loss_grad_theta = np.array([1.0, 0.0, 0.0, 0.0])
        train_loss_grad_theta_grad_w = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        train_loss_hessian_theta = np.eye(D)
        
        result = fn(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        # Expected: -[1, 0, 0, 0]^T @ I^{-1} @ [[0,0,0], [1,0,0], [0,1,0], [0,0,1]]
        #         = -[1, 0, 0, 0]^T @ [[0,0,0], [1,0,0], [0,1,0], [0,0,1]]
        #         = -[0, 0, 0] = [0, 0, 0]
        expected = np.zeros(N)
        error = np.linalg.norm(result - expected)
        passed = error < 1e-6
        results.append({
            "name": "Orthogonal vectors with identity Hessian",
            "passed": passed,
            "detail": f"Error from zero: {error}, result: {result}"
        })
    except Exception as e:
        results.append({
            "name": "Orthogonal vectors with identity Hessian",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Consistency with explicit formula for small case
    # Verify against explicit computation: -val_loss_grad_theta^T @ inv(H) @ train_loss_grad_theta_grad_w
    try:
        np.random.seed(46)
        D, N = 3, 2
        val_loss_grad_theta = np.random.randn(D)
        train_loss_hessian_theta = np.random.randn(D, D)
        train_loss_hessian_theta = train_loss_hessian_theta @ train_loss_hessian_theta.T
        train_loss_grad_theta_grad_w = np.random.randn(D, N)
        
        result = fn(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w)
        
        # Explicit computation
        H_inv = np.linalg.inv(train_loss_hessian_theta)
        expected = -val_loss_grad_theta @ H_inv @ train_loss_grad_theta_grad_w
        
        error = np.linalg.norm(result - expected)
        passed = error < 1e-6
        results.append({
            "name": "Consistency with explicit formula",
            "passed": passed,
            "detail": f"Error: {error}"
        })
    except Exception as e:
        results.append({
            "name": "Consistency with explicit formula",
            "passed": False,
            "detail": str(e)
        })
    
    return results
