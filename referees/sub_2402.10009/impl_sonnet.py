import numpy as np


def compute_shifted_x0_prediction(x_t, f_t_x_t_shifted, alpha_bar_t):
    """
    Compute the x0 prediction from shifted x_t in DDPM inversion.
    
    This implements line 22 of Algorithm 1 from the ZEUS paper:
    x_{0|t}^shifted = (x_t^shifted - sqrt(1 - alpha_bar_t) * f_t(x_t^shifted)) / sqrt(alpha_bar_t)
    
    Args:
        x_t: array of shape (D,) representing the shifted noisy latent x_t_shifted at timestep t
        f_t_x_t_shifted: array of shape (D,) representing the denoiser output f_t(x_t_shifted)
        alpha_bar_t: scalar float, the cumulative product of alphas at timestep t (0 < alpha_bar_t <= 1)
    
    Returns:
        array of shape (D,) representing the predicted x0 from the shifted latent
    """
    # Convert inputs to numpy arrays with float dtype
    x_t = np.asarray(x_t, dtype=float)
    f_t_x_t_shifted = np.asarray(f_t_x_t_shifted, dtype=float)
    alpha_bar_t = float(alpha_bar_t)
    
    # Compute sqrt(1 - alpha_bar_t)
    sqrt_one_minus_alpha_bar_t = np.sqrt(1.0 - alpha_bar_t)
    
    # Compute sqrt(alpha_bar_t)
    sqrt_alpha_bar_t = np.sqrt(alpha_bar_t)
    
    # Compute x0_shifted = (x_t - sqrt(1 - alpha_bar_t) * f_t(x_t_shifted)) / sqrt(alpha_bar_t)
    x0_shifted = (x_t - sqrt_one_minus_alpha_bar_t * f_t_x_t_shifted) / sqrt_alpha_bar_t
    
    return x0_shifted
