import numpy as np

def ddim_step(x_t, x_pred, t_now, t_next, ns, ds, scale):
    """
    Compute one DDIM denoising step.
    
    Args:
        x_t: Current noisy sample at time t_now
        x_pred: Predicted clean sample
        t_now: Current time step
        t_next: Next time step
        ns: Scheduling parameter (default 0.0002)
        ds: Scheduling parameter (default 0.00025)
        scale: Clipping scale
    
    Returns:
        x_next: Denoised sample at time t_next
    """
    # Convert inputs to numpy arrays
    x_t = np.asarray(x_t, dtype=float)
    x_pred = np.asarray(x_pred, dtype=float)
    t_now = float(t_now)
    t_next = float(t_next)
    ns = float(ns)
    ds = float(ds)
    scale = float(scale)
    
    # Compute gamma_now and gamma_next using cosine scheduling
    gamma_now = np.cos(((t_now + ns) / (1 + ds)) * np.pi / 2) ** 2
    gamma_next = np.cos(((t_next + ns) / (1 + ds)) * np.pi / 2) ** 2
    
    # Clip x_pred to [-scale, scale]
    x_pred_clipped = np.clip(x_pred, -scale, scale)
    
    # Compute eps (noise estimate)
    eps = (x_t - np.sqrt(gamma_now) * x_pred_clipped) / np.sqrt(1 - gamma_now)
    
    # Compute x_next using DDIM update rule
    x_next = np.sqrt(gamma_next) * x_pred_clipped + np.sqrt(1 - gamma_next) * eps
    
    return x_next
