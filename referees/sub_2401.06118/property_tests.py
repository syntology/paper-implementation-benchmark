import numpy as np

def check(fn):
    results = []
    np.random.seed(42)
    
    # Test 1: Non-negativity of loss
    try:
        n_out, n_in, n_codebooks, codebook_size = 3, 4, 2, 8
        X_gram = np.random.randn(n_in, n_in)
        X_gram = X_gram @ X_gram.T  # Make positive semi-definite
        W = np.random.randn(n_out, n_in)
        C = np.random.randn(n_codebooks, codebook_size, n_out, n_in)
        b = np.random.randint(0, codebook_size, size=(n_out, n_in, n_codebooks))
        s = np.random.randn(n_out, n_in, n_codebooks)
        
        loss = fn(X_gram, W, C, b, s)
        passed = loss >= -1e-6  # Allow small numerical error
        results.append({
            "name": "non_negativity",
            "passed": bool(passed),
            "detail": f"Loss should be non-negative (trace of quadratic form with PSD matrix), got {loss}"
        })
    except Exception as e:
        results.append({"name": "non_negativity", "passed": False, "detail": str(e)})
    
    # Test 2: Perfect reconstruction gives zero loss
    try:
        n_out, n_in, n_codebooks, codebook_size = 3, 4, 2, 8
        X_gram = np.random.randn(n_in, n_in)
        X_gram = X_gram @ X_gram.T
        W = np.random.randn(n_out, n_in)
        C = np.random.randn(n_codebooks, codebook_size, n_out, n_in)
        b = np.random.randint(0, codebook_size, size=(n_out, n_in, n_codebooks))
        s = np.random.randn(n_out, n_in, n_codebooks)
        
        # Construct W_hat and set W = W_hat for perfect reconstruction
        W_hat = np.zeros((n_out, n_in))
        for i in range(n_out):
            for j in range(n_in):
                for k in range(n_codebooks):
                    W_hat[i, j] += s[i, j, k] * C[k, b[i, j, k], i, j]
        W = W_hat.copy()
        
        loss = fn(X_gram, W, C, b, s)
        passed = abs(loss) < 1e-6
        results.append({
            "name": "perfect_reconstruction_zero_loss",
            "passed": bool(passed),
            "detail": f"Perfect reconstruction should give zero loss, got {loss}"
        })
    except Exception as e:
        results.append({"name": "perfect_reconstruction_zero_loss", "passed": False, "detail": str(e)})
    
    # Test 3: Scaling property - scaling X_gram scales loss
    try:
        n_out, n_in, n_codebooks, codebook_size = 3, 4, 2, 8
        X_gram = np.random.randn(n_in, n_in)
        X_gram = X_gram @ X_gram.T
        W = np.random.randn(n_out, n_in)
        C = np.random.randn(n_codebooks, codebook_size, n_out, n_in)
        b = np.random.randint(0, codebook_size, size=(n_out, n_in, n_codebooks))
        s = np.random.randn(n_out, n_in, n_codebooks)
        
        loss1 = fn(X_gram, W, C, b, s)
        alpha = 2.5
        loss2 = fn(alpha * X_gram, W, C, b, s)
        
        expected_loss2 = alpha * loss1
        passed = abs(loss2 - expected_loss2) < 1e-6 * abs(expected_loss2) + 1e-6
        results.append({
            "name": "x_gram_scaling_property",
            "passed": bool(passed),
            "detail": f"Scaling X_gram by {alpha} should scale loss by {alpha}: got {loss2}, expected {expected_loss2}"
        })
    except Exception as e:
        results.append({"name": "x_gram_scaling_property", "passed": False, "detail": str(e)})
    
    # Test 4: Zero X_gram gives zero loss
    try:
        n_out, n_in, n_codebooks, codebook_size = 3, 4, 2, 8
        X_gram = np.zeros((n_in, n_in))
        W = np.random.randn(n_out, n_in)
        C = np.random.randn(n_codebooks, codebook_size, n_out, n_in)
        b = np.random.randint(0, codebook_size, size=(n_out, n_in, n_codebooks))
        s = np.random.randn(n_out, n_in, n_codebooks)
        
        loss = fn(X_gram, W, C, b, s)
        passed = abs(loss) < 1e-6
        results.append({
            "name": "zero_x_gram_zero_loss",
            "passed": bool(passed),
            "detail": f"Zero X_gram should give zero loss (no input statistics), got {loss}"
        })
    except Exception as e:
        results.append({"name": "zero_x_gram_zero_loss", "passed": False, "detail": str(e)})
    
    # Test 5: Scaling factors linearity - scaling all s by alpha scales W_hat by alpha
    try:
        n_out, n_in, n_codebooks, codebook_size = 3, 4, 2, 8
        X_gram = np.random.randn(n_in, n_in)
        X_gram = X_gram @ X_gram.T
        W = np.random.randn(n_out, n_in)
        C = np.random.randn(n_codebooks, codebook_size, n_out, n_in)
        b = np.random.randint(0, codebook_size, size=(n_out, n_in, n_codebooks))
        s = np.random.randn(n_out, n_in, n_codebooks)
        
        # Compute W_hat for original s
        W_hat1 = np.zeros((n_out, n_in))
        for i in range(n_out):
            for j in range(n_in):
                for k in range(n_codebooks):
                    W_hat1[i, j] += s[i, j, k] * C[k, b[i, j, k], i, j]
        
        # Scale s and compute loss
        alpha = 2.0
        s_scaled = alpha * s
        loss_scaled = fn(X_gram, W, C, b, s_scaled)
        
        # Expected: W_hat becomes alpha * W_hat1, so error is (alpha * W_hat1 - W)
        # Loss should be trace((alpha*W_hat1 - W) @ X_gram @ (alpha*W_hat1 - W)^T)
        diff = alpha * W_hat1 - W
        expected_loss = np.trace(diff @ X_gram @ diff.T)
        
        passed = abs(loss_scaled - expected_loss) < 1e-6 * abs(expected_loss) + 1e-6
        results.append({
            "name": "scaling_factors_linearity",
            "passed": bool(passed),
            "detail": f"Scaling all s by {alpha} should give predictable loss: got {loss_scaled}, expected {expected_loss}"
        })
    except Exception as e:
        results.append({"name": "scaling_factors_linearity", "passed": False, "detail": str(e)})
    
    return results
