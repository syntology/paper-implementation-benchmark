import numpy as np

def gamma(t, ns=0.0002, ds=0.00025):
    """
    A scheduling function based on cosine function.
    
    Parameters:
    t (float): time
    ns (float, optional): noise schedule parameter. Defaults to 0.0002.
    ds (float, optional): diffusion schedule parameter. Defaults to 0.00025.
    
    Returns:
    float: gamma value
    """
    return np.cos(((t + ns) / (1 + ds)) * np.pi / 2)**2

def ddim_step(x_t, x_pred, t_now, t_next, ns=0.0002, ds=0.00025, scale=1.0):
    """
    Compute a single DDIM denoising step.
    
    Parameters:
    x_t (numpy array): current noisy sample
    x_pred (numpy array): predicted clean sample
    t_now (float): current time
    t_next (float): next time
    ns (float, optional): noise schedule parameter. Defaults to 0.0002.
    ds (float, optional): diffusion schedule parameter. Defaults to 0.00025.
    scale (float, optional): clipping scale. Defaults to 1.0.
    
    Returns:
    numpy array: x_next at time t_next using the DDIM updating rule
    """
    # Convert array-like arguments to numpy arrays with float64 dtype
    x_t = np.asarray(x_t, dtype=np.float64)
    x_pred = np.asarray(x_pred, dtype=np.float64)
    
    # Compute gamma_now and gamma_next using the cosine schedule
    gamma_now = gamma(t_now, ns, ds)
    gamma_next = gamma(t_next, ns, ds)
    
    # Clip x_pred element-wise to the range [-scale, scale]
    x_pred = np.clip(x_pred, -scale, scale)
    
    # Compute the noise estimate eps
    eps = (x_t - np.sqrt(gamma_now) * x_pred) / np.sqrt(1 - gamma_now)
    
    # Compute x_next
    x_next = np.sqrt(gamma_next) * x_pred + np.sqrt(1 - gamma_next) * eps
    
    return x_next
