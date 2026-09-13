import numpy as np

def compute_shifted_x0_prediction(x_t, f_t_x_t_shifted, alpha_bar_t):
    """
    Compute the x0 prediction from shifted x_t in DDPM inversion.

    Parameters:
    x_t (array-like): array of shape (D,) representing the shifted noisy latent x_t_shifted at timestep t
    f_t_x_t_shifted (array-like): array of shape (D,) representing the denoiser output f_t(x_t_shifted) already evaluated at the shifted input
    alpha_bar_t (float): scalar float, the cumulative product of alphas at timestep t, must satisfy 0 < alpha_bar_t <= 1

    Returns:
    array of shape (D,) representing the predicted x0 from the shifted latent
    """
    x_t = np.asarray(x_t, dtype=float)
    f_t_x_t_shifted = np.asarray(f_t_x_t_shifted, dtype=float)
    
    # Compute x0_shifted = (x_t - sqrt(1 - alpha_bar_t) * f_t_x_t_shifted) / sqrt(alpha_bar_t)
    x0_shifted = (x_t - np.sqrt(1 - alpha_bar_t) * f_t_x_t_shifted) / np.sqrt(alpha_bar_t)
    
    return x0_shifted
