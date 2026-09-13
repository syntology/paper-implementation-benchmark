import numpy as np

def noise_cancellation_correction(eps_hat, eps_init, eps_noises, eps_step_size, ld_steps):
    """
    Compute the noise-cancelled epsilon correction used in EM Distillation MCMC.
    
    Args:
        eps_hat: array of shape (B, D1, ..., Dk) - final epsilon after ld_steps Langevin updates
        eps_init: array of shape (B, D1, ..., Dk) - initial epsilon before Langevin updates
        eps_noises: array of shape (ld_steps, B, D1, ..., Dk) - pre-sampled Gaussian noises
        eps_step_size: scalar float - step size used in epsilon Langevin dynamics
        ld_steps: integer - number of Langevin dynamics steps performed
    
    Returns:
        array of shape (B, D1, ..., Dk) - noise-cancelled epsilon correction
    """
    # Convert inputs to numpy arrays with float dtype
    eps_hat = np.asarray(eps_hat, dtype=float)
    eps_init = np.asarray(eps_init, dtype=float)
    eps_noises = np.asarray(eps_noises, dtype=float)
    eps_step_size = float(eps_step_size)
    ld_steps = int(ld_steps)
    
    # Step 1: Start with result = eps_hat
    result = eps_hat.copy()
    
    # Step 2: Subtract the decayed initial noise
    decay_factor = (1 - eps_step_size ** 2) ** ld_steps
    result = result - decay_factor * eps_init
    
    # Step 3: Compute step_weights as a 1D array
    # step_weights[i] = (1 - eps_step_size^2)^(ld_steps - 1 - i) for i in range(ld_steps)
    # This creates: [(1-h^2)^(L-1), (1-h^2)^(L-2), ..., (1-h^2)^0]
    exponents = np.arange(ld_steps - 1, -1, -1)  # [L-1, L-2, ..., 1, 0]
    step_weights = (1 - eps_step_size ** 2) ** exponents
    
    # Step 4: Broadcast step_weights to match eps_noises dimensions
    # eps_noises has shape (ld_steps, B, D1, ..., Dk)
    # We need step_weights to have shape (ld_steps, 1, 1, ..., 1)
    new_shape = [ld_steps] + [1] * (eps_noises.ndim - 1)
    step_weights = step_weights.reshape(new_shape)
    
    # Step 5: Compute weighted_noises
    weighted_noises = eps_step_size * step_weights * eps_noises
    
    # Step 6: Sum over the first axis (ld_steps dimension)
    noise_sum = np.sum(weighted_noises, axis=0)
    
    # Step 7: Subtract sqrt(2) * noise_sum from result
    result = result - np.sqrt(2) * noise_sum
    
    return result
