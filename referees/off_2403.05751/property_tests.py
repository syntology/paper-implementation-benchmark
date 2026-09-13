import numpy as np

def check(fn):
    results = []
    
    # Test 1: Loss is non-negative (MSE property)
    try:
        np.random.seed(42)
        G, D, H = 3, 5, 4
        x_t_g = np.random.randn(G, D)
        epsilon = np.random.randn(G, D)
        alpha_bar_n_g = np.random.uniform(0.1, 0.9, G)
        h_t_g = np.random.randn(G, H)
        theta_g = np.random.randn(G, H, D)
        
        loss = fn(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g)
        
        passed = loss >= 0.0
        detail = f"Loss = {loss}; expected >= 0" if not passed else "Loss is non-negative"
        results.append({"name": "Loss is non-negative", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Loss is non-negative", "passed": False, "detail": str(e)})
    
    # Test 2: Loss is zero when epsilon equals epsilon_pred
    try:
        np.random.seed(43)
        G, D, H = 2, 4, 3
        h_t_g = np.random.randn(G, H)
        theta_g = np.random.randn(G, H, D)
        
        # Construct epsilon such that it equals theta_g @ h_t_g
        epsilon = np.array([theta_g[g] @ h_t_g[g] for g in range(G)])
        
        x_t_g = np.random.randn(G, D)
        alpha_bar_n_g = np.random.uniform(0.1, 0.9, G)
        
        loss = fn(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g)
        
        passed = np.abs(loss) < 1e-6
        detail = f"Loss = {loss}; expected ~0" if not passed else "Loss is zero when epsilon matches prediction"
        results.append({"name": "Loss is zero when epsilon equals epsilon_pred", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Loss is zero when epsilon equals epsilon_pred", "passed": False, "detail": str(e)})
    
    # Test 3: Loss is invariant to scaling of theta_g and h_t_g together
    try:
        np.random.seed(44)
        G, D, H = 2, 3, 2
        x_t_g = np.random.randn(G, D)
        epsilon = np.random.randn(G, D)
        alpha_bar_n_g = np.random.uniform(0.1, 0.9, G)
        h_t_g = np.random.randn(G, H)
        theta_g = np.random.randn(G, H, D)
        
        loss1 = fn(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g)
        
        # Scale both h_t_g and theta_g by same factor (should scale loss by factor^2)
        scale = 2.5
        h_t_g_scaled = h_t_g * scale
        theta_g_scaled = theta_g / scale  # inverse scale to keep product same
        
        loss2 = fn(x_t_g, epsilon, alpha_bar_n_g, h_t_g_scaled, theta_g_scaled)
        
        passed = np.abs(loss1 - loss2) < 1e-6
        detail = f"Loss1 = {loss1}, Loss2 = {loss2}; expected equal" if not passed else "Loss invariant to compensating scaling"
        results.append({"name": "Loss invariant to compensating h_t_g and theta_g scaling", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Loss invariant to compensating h_t_g and theta_g scaling", "passed": False, "detail": str(e)})
    
    # Test 4: Loss scales quadratically with epsilon perturbation
    try:
        np.random.seed(45)
        G, D, H = 2, 3, 2
        x_t_g = np.random.randn(G, D)
        epsilon_base = np.random.randn(G, D)
        alpha_bar_n_g = np.random.uniform(0.1, 0.9, G)
        h_t_g = np.random.randn(G, H)
        theta_g = np.zeros((G, H, D))  # Zero theta so epsilon_pred = 0
        
        loss_base = fn(x_t_g, epsilon_base, alpha_bar_n_g, h_t_g, theta_g)
        
        # Scale epsilon by factor k
        k = 3.0
        epsilon_scaled = epsilon_base * k
        loss_scaled = fn(x_t_g, epsilon_scaled, alpha_bar_n_g, h_t_g, theta_g)
        
        # Loss should scale by k^2
        expected_ratio = k ** 2
        actual_ratio = loss_scaled / (loss_base + 1e-10)
        
        passed = np.abs(actual_ratio - expected_ratio) < 1e-5
        detail = f"Ratio = {actual_ratio}; expected {expected_ratio}" if not passed else "Loss scales quadratically with epsilon"
        results.append({"name": "Loss scales quadratically with epsilon magnitude", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Loss scales quadratically with epsilon magnitude", "passed": False, "detail": str(e)})
    
    # Test 5: Loss is average over granularities (decomposability)
    try:
        np.random.seed(46)
        G, D, H = 3, 4, 2
        x_t_g = np.random.randn(G, D)
        epsilon = np.random.randn(G, D)
        alpha_bar_n_g = np.random.uniform(0.1, 0.9, G)
        h_t_g = np.random.randn(G, H)
        theta_g = np.random.randn(G, H, D)
        
        total_loss = fn(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g)
        
        # Compute per-granularity losses manually
        per_g_losses = []
        for g in range(G):
            epsilon_pred_g = theta_g[g] @ h_t_g[g]
            mse_g = np.mean((epsilon[g] - epsilon_pred_g) ** 2)
            per_g_losses.append(mse_g)
        
        expected_loss = np.mean(per_g_losses)
        
        passed = np.abs(total_loss - expected_loss) < 1e-6
        detail = f"Total loss = {total_loss}, expected = {expected_loss}" if not passed else "Loss correctly averages over granularities"
        results.append({"name": "Loss is mean over granularities", "passed": passed, "detail": detail})
    except Exception as e:
        results.append({"name": "Loss is mean over granularities", "passed": False, "detail": str(e)})
    
    return results
