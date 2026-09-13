import numpy as np

def estimate_python_proportion(loss_j, alpha, beta):
    """
    Estimate the proportion of the Python system based on Equation 1 from the paper.

    Parameters:
    loss_j (float): The training loss at checkpoint j.
    alpha (float): The initial loss.
    beta (float): The lowest loss.

    Returns:
    float: The proportion of the Python system.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    loss_j = np.asarray(loss_j, dtype=float)
    alpha = np.asarray(alpha, dtype=float)
    beta = np.asarray(beta, dtype=float)

    # Compute the proportion using the formula
    proportion = (alpha - loss_j) / (alpha - beta)

    # Clip the proportion to [0, 1] to handle edge cases
    proportion = np.clip(proportion, 0, 1)

    # Return a plain Python float for scalar results
    return float(proportion)
