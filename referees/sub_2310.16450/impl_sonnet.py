import numpy as np


def calculate_clex_theta(t_prime, t_train, d_model, lambda_factor):
    """
    Calculate the CLEX position encoding scaling vector theta at time t_prime.
    
    Args:
        t_prime: scalar, dimensionless time in range [1, t_train]
        t_train: scalar, maximum training time
        d_model: integer, model dimension (must be even)
        lambda_factor: scalar, the lambda hyperparameter controlling interpolation speed
    
    Returns:
        1D numpy array of shape (d_model/2,) containing the scaled theta values in float64
    """
    # Convert inputs to appropriate types
    t_prime = float(t_prime)
    t_train = float(t_train)
    d_model = int(d_model)
    lambda_factor = float(lambda_factor)
    
    # Calculate z(t_prime) using the ODE solution
    # z(t) = log(1 + (t - 1) * lambda) when lambda > 0
    z_t_prime = np.log(1.0 + (t_prime - 1.0) * lambda_factor)
    
    # Calculate exp(z(t_prime)) which is the scaling factor
    exp_z_t_prime = np.exp(z_t_prime)
    
    # Calculate the number of theta dimensions
    n_dims = d_model // 2
    
    # Calculate base theta values for RoPE
    # theta_base[i] = 10000^(-2i/d_model) for i in [0, d_model/2 - 1]
    i = np.arange(n_dims, dtype=np.float64)
    theta_base = np.power(10000.0, -2.0 * i / d_model)
    
    # Calculate CLEX theta: theta_{t_prime}[i] = theta_base[i] * exp(z(t_prime))
    theta_t_prime = theta_base * exp_z_t_prime
    
    return theta_t_prime
