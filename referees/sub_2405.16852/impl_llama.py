import numpy as np

def noise_cancellation_correction(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps):
    """
    Compute the noise-cancelled epsilon correction used in EM Distillation MCMC.

    Parameters:
    eps_hat (array): array of shape (B, D1, ..., Dk) representing the final epsilon after ld_steps Langevin updates
    eps_init (array): array of shape (B, D1, ..., Dk) representing the initial epsilon before Langevin updates
    eps_noises (array): array of shape (ld_steps, B, D1, ..., Dk) containing pre-sampled Gaussian noises used in each Langevin step, indexed [step, batch, ...]
    eps_step_size (float): scalar float, the step size used in epsilon Langevin dynamics
    ld_steps (int): integer, the number of Langevin dynamics steps performed

    Returns:
    array: array of shape (B, D1, ..., Dk) containing the noise-cancelled epsilon correction
    """
    eps_hat = np.asarray(eps_hat, dtype=float)
    eps_init = np.asarray(eps_init, dtype=float)
    eps_noises = np.asarray(eps_noises, dtype=float)
    eps_step_size = float(eps_step_size)
    ld_steps = int(ld_steps)

    result = eps_hat
    result = result - (1 - eps_step_size**2)**ld_steps * eps_init

    step_weights = (1 - eps_step_size**2)**np.arange(ld_steps - 1, -1, -1)
    step_weights = np.reshape(step_weights, (ld_steps,) + (1,) * (eps_noises.ndim - 1))

    weighted_noises = eps_step_size * step_weights * eps_noises
    noise_sum = np.sum(weighted_noises, axis=0)

    result = result - np.sqrt(2) * noise_sum

    return result
