import numpy as np

def compute_layer_output_with_filter_subset(z_in, theta, filter_indices):
    """
    Compute the output of a neural network layer using only a subset of filters (or neurons), 
    averaged by the subset size.

    Parameters:
    z_in (array-like): Input of shape (batch_size, input_dim)
    theta (array-like): Weight parameters of shape (num_filters, input_dim)
    filter_indices (list): List of 0-based filter indices to include

    Returns:
    array: Output of shape (batch_size, num_filters) where each column corresponds to one filter 
           in the original layer.
    """
    z_in = np.asarray(z_in, dtype=float)
    theta = np.asarray(theta, dtype=float)
    filter_indices = np.asarray(filter_indices, dtype=int)

    # Convert filter_indices to a set for efficient lookups
    filter_indices_set = set(filter_indices)

    # Initialize output array with zeros
    output = np.zeros((z_in.shape[0], theta.shape[0]))

    # If filter_indices is empty, return zeros
    if len(filter_indices) == 0:
        return output

    # Compute the output for the selected filters
    selected_filter_outputs = []
    for j in filter_indices:
        # Compute the linear transformation
        linear_transform = np.dot(theta[j], z_in.T)
        # Apply ReLU activation
        activation = np.maximum(0, linear_transform)
        selected_filter_outputs.append(activation)

    # Sum all selected filter outputs and divide by the number of selected filters
    averaged_output = np.sum(selected_filter_outputs, axis=0) / len(filter_indices)

    # Fill the output array with the averaged result for the selected filters
    for j in filter_indices_set:
        output[:, j] = averaged_output

    return output
