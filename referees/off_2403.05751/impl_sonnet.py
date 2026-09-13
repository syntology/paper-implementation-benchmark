import numpy as np


def compute_diffusion_loss_step(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g):
    """
    Compute the diffusion loss for a single time step t and diffusion step n
    across G granularities.
    
    Args:
        x_t_g: shape (G, D) - original data at time t for each granularity
        epsilon: shape (G, D) - sampled noise from standard normal
        alpha_bar_n_g: shape (G,) - cumulative product of alphas up to step n
        h_t_g: shape (G, H) - RNN hidden states at time t for each granularity
        theta_g: shape (G, H, D) - learned denoising network parameters
    
    Returns:
        float: scalar loss value
    """
    # Convert inputs to numpy arrays with float dtype
    x_t_g = np.asarray(x_t_g, dtype=float)
    epsilon = np.asarray(epsilon, dtype=float)
    alpha_bar_n_g = np.asarray(alpha_bar_n_g, dtype=float)
    h_t_g = np.asarray(h_t_g, dtype=float)
    theta_g = np.asarray(theta_g, dtype=float)
    
    # Get dimensions
    G, D = x_t_g.shape
    
    # Forward diffusion: x_n = sqrt(alpha_bar_n) * x_0 + sqrt(1 - alpha_bar_n) * epsilon
    # This step is implicit in the loss computation (we already have epsilon)
    
    # Predict noise using the denoising network
    # epsilon_pred[g] = theta_g[g] @ h_t_g[g]
    # theta_g has shape (G, H, D), h_t_g has shape (G, H)
    # For each g: theta_g[g] is (H, D), h_t_g[g] is (H,)
    # Result should be (D,) for each g
    epsilon_pred = np.zeros((G, D), dtype=float)
    for g in range(G):
        # Matrix-vector multiplication: (H, D).T @ (H,) = (D, H) @ (H,) = (D,)
        epsilon_pred[g] = theta_g[g].T @ h_t_g[g]
    
    # Compute mean squared error loss
    # L = (1/G) * sum_g (1/D) * sum_d (epsilon[g,d] - epsilon_pred[g,d])^2
    squared_errors = (epsilon - epsilon_pred) ** 2
    loss = np.mean(squared_errors)
    
    # Return as plain Python float
    return float(loss)
