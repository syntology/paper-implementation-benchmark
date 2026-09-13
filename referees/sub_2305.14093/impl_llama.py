import numpy as np

def aggregate_multiscale_patch_features(patch_features, patch_coords, image_height, image_width, feature_dim):
    """
    Aggregate overlapping patch features into a single spatial feature map by averaging.

    Args:
    patch_features (list of 1D arrays): CLIP feature vectors for each patch.
    patch_coords (list of 4-tuples): Pixel coordinates for each patch.
    image_height (int): Height of the image.
    image_width (int): Width of the image.
    feature_dim (int): Dimension of the feature vectors.

    Returns:
    A 3D numpy array of shape (1, feature_dim, image_height, image_width) representing the aggregated feature map.
    """

    # Convert array-like arguments to numpy arrays with float64 dtype
    patch_features = np.asarray(patch_features, dtype=float)
    patch_coords = np.asarray(patch_coords, dtype=int)

    # Initialize sum and count arrays
    sum_array = np.zeros((1, feature_dim, image_height, image_width), dtype=float)
    count_array = np.zeros((1, 1, image_height, image_width), dtype=float)

    # Iterate over each patch feature and its coordinates
    for feature, (left, upper, right, lower) in zip(patch_features, patch_coords):
        # Add the feature vector to the sum array and increment the count array
        sum_array[:, :, upper:lower, left:right] += feature[np.newaxis, :, np.newaxis, np.newaxis]
        count_array[:, :, upper:lower, left:right] += 1

    # Divide the sum array by the count array, handling division by zero
    aggregated_features = np.where(count_array > 0, sum_array / count_array, 0)

    return aggregated_features
