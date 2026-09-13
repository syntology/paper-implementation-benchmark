import numpy as np

def compute_diffusion_loss_step(x_t_g, epsilon, alpha_bar_n_g, h_t_g, theta_g):
    """
    Compute the diffusion loss for a single time step t and diffusion step n across G granularities.

    Parameters:
    x_t_g (array-like): shape (G, D) where G is number of granularities and D is feature dimension at time t
    epsilon (array-like): shape (G, D) sampled from standard normal
    alpha_bar_n_g (array-like): shape (G,) containing cumulative product of alphas up to step n for each granularity
    h_t_g (array-like): shape (G, H) containing RNN hidden states at time t for each granularity
    theta_g (array-like): shape (G, H, D) containing learned denoising network parameters

    Returns:
    float: the mean squared error loss
    """
    x_t_g = np.asarray(x_t_g, dtype=float)
    epsilon = np.asarray(epsilon, dtype=float)
    alpha_bar_n_g = np.asarray(alpha_bar_n_g, dtype=float)
    h_t_g = np.asarray(h_t_g, dtype=float)
    theta_g = np.asarray(theta_g, dtype=float)

    G, D = x_t_g.shape
    H = h_t_g.shape[1]

    # Compute the forward diffusion
    x_n_g = np.sqrt(alpha_bar_n_g[:, np.newaxis]) * x_t_g + np.sqrt(1 - alpha_bar_n_g[:, np.newaxis]) * epsilon

    # Compute the predicted noise
    epsilon_pred_g = np.einsum('ghd,gh->gd', theta_g, h_t_g)

    # Compute the mean squared error loss
    loss = np.mean((epsilon - epsilon_pred_g) ** 2)

    return float(loss)
