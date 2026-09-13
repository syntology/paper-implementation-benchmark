import numpy as np


def compute_layer_output_with_filter_subset(z_in, theta, filter_indices):
    """
    Compute the output of a neural network layer using only a subset of filters,
    averaged by the subset size, as described in the Greedy Forward Selection algorithm.
    
    Args:
        z_in: Input array of shape (batch_size, input_dim)
        theta: Weight parameters of shape (num_filters, input_dim)
        filter_indices: List of 0-based filter indices to include in the subset
    
    Returns:
        Array of shape (batch_size, num_filters) where:
        - Filters in filter_indices contain the averaged activation
        - Filters not in filter_indices contain 0
    """
    # Convert inputs to numpy arrays with float dtype
    z_in = np.asarray(z_in, dtype=float)
    theta = np.asarray(theta, dtype=float)
    filter_indices = list(filter_indices) if not isinstance(filter_indices, list) else filter_indices
    
    batch_size = z_in.shape[0]
    num_filters = theta.shape[0]
    
    # Initialize output with zeros
    output = np.zeros((batch_size, num_filters), dtype=float)
    
    # If no filters selected, return zeros
    if len(filter_indices) == 0:
        return output
    
    # Compute the averaged activation for selected filters
    # sum_{j in S} sigma(theta_j, z_in) / |S|
    averaged_activation = np.zeros(batch_size, dtype=float)
    
    for j in filter_indices:
        # Linear transformation: theta[j] @ z_in.T
        # theta[j] has shape (input_dim,)
        # z_in.T has shape (input_dim, batch_size)
        # Result has shape (batch_size,)
        linear_output = np.dot(z_in, theta[j])
        
        # Apply ReLU activation: max(0, x)
        activated_output = np.maximum(0, linear_output)
        
        # Accumulate
        averaged_activation += activated_output
    
    # Divide by the number of selected filters
    averaged_activation /= len(filter_indices)
    
    # Replicate the averaged result to all selected filter positions
    for j in filter_indices:
        output[:, j] = averaged_activation
    
    return output
