import numpy as np

def calculate_clex_theta(t_prime, t_train, d_model, lambda_factor):
    """
    Calculate the CLEX position encoding scaling vector theta at a given time point t_prime.

    Parameters:
    t_prime (float): dimensionless time in range [1, t_train]
    t_train (float): maximum training time
    d_model (int): model dimension, must be even
    lambda_factor (float): the lambda hyperparameter controlling interpolation speed

    Returns:
    np.ndarray: a 1D numpy array of shape (d_model/2,) containing the scaled theta values in float64
    """
    t_prime = np.asarray(t_prime, dtype=float)
    t_train = np.asarray(t_train, dtype=float)
    d_model = int(d_model)
    lambda_factor = np.asarray(lambda_factor, dtype=float)

    # Calculate lambda
    lambda_val = lambda_factor

    # Calculate z(t_prime)
    z_t_prime = np.log(1 + (t_prime - 1) * lambda_val)

    # Calculate theta_base
    theta_base = 10000 ** (-2 * np.arange(d_model // 2) / d_model)

    # Calculate theta_{t_prime}
    theta_t_prime = theta_base * np.exp(z_t_prime)

    return theta_t_prime

# Helper function to calculate z(t)
def calculate_z(t, lambda_val):
    """
    Calculate z(t) = log(1 + (t - 1) * lambda)

    Parameters:
    t (float): dimensionless time
    lambda_val (float): the lambda hyperparameter controlling interpolation speed

    Returns:
    float: z(t)
    """
    return np.log(1 + (t - 1) * lambda_val)
