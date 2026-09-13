import numpy as np

def aggregate_multiscale_patch_features(patch_features, patch_coords, image_height, image_width, feature_dim):
    """
    Aggregate overlapping patch features into a single spatial feature map by averaging.
    
    Args:
        patch_features: List of 1D arrays, each of shape (feature_dim,) representing CLIP feature vector for one patch
        patch_coords: List of 4-tuples (left, upper, right, lower) in pixel coordinates
        image_height: Height of the output image
        image_width: Width of the output image
        feature_dim: Dimension of the feature vectors
    
    Returns:
        Aggregated feature map of shape (1, feature_dim, image_height, image_width) with dtype float64
    """
    # Initialize sum array and count array
    sum_array = np.zeros((1, feature_dim, image_height, image_width), dtype=np.float64)
    count_array = np.zeros((1, 1, image_height, image_width), dtype=np.float64)
    
    # Loop over all patches
    for patch_feature, coords in zip(patch_features, patch_coords):
        # Convert patch_feature to numpy array with float dtype
        patch_feature = np.asarray(patch_feature, dtype=np.float64)
        
        # Extract coordinates
        left, upper, right, lower = coords
        
        # Ensure coordinates are integers
        left, upper, right, lower = int(left), int(upper), int(right), int(lower)
        
        # Add patch feature to sum array (broadcast feature vector to spatial dimensions)
        # patch_feature has shape (feature_dim,)
        # We need to broadcast it to shape (1, feature_dim, lower-upper, right-left)
        sum_array[:, :, upper:lower, left:right] += patch_feature.reshape(1, feature_dim, 1, 1)
        
        # Increment count for this region
        count_array[:, :, upper:lower, left:right] += 1
    
    # Divide sum by count element-wise, handling division by zero
    # Where count is 0, the result should be 0
    with np.errstate(divide='ignore', invalid='ignore'):
        result = sum_array / count_array
        # Replace NaN and Inf with 0
        result = np.where(np.isfinite(result), result, 0.0)
    
    return result
