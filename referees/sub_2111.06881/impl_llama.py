import numpy as np

def unproject_2d_point_with_depth(point_2d, depth, projection_matrix, transform_matrix):
    """
    Unproject a 2D image point to 3D space using a given depth value.

    Args:
    point_2d (array-like): A length-2 array [u, v] in pixel coordinates (0-indexed).
    depth (float): A scalar float representing the distance along the ray.
    projection_matrix (array-like): A 4x4 camera projection matrix P_rgb.
    transform_matrix (array-like): A 4x4 transformation matrix T from lidar to camera coordinates.

    Returns:
    array: A length-3 array [x/w, y/w, z/w] representing the 3D point in lidar coordinate frame.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    point_2d = np.asarray(point_2d, dtype=float)
    projection_matrix = np.asarray(projection_matrix, dtype=float)
    transform_matrix = np.asarray(transform_matrix, dtype=float)

    # Create homogeneous 2D point [u, v, 1]
    point_2d_homogeneous = np.array([point_2d[0], point_2d[1], 1])

    # Multiply by depth to get [u*depth, v*depth, depth]
    point_2d_depth = point_2d_homogeneous * depth

    # Create 4D homogeneous point [u*depth, v*depth, depth, 1]
    point_4d = np.array([point_2d_depth[0], point_2d_depth[1], point_2d_depth[2], 1])

    # Compute the combined transformation matrix M = projection_matrix @ transform_matrix
    combined_matrix = projection_matrix @ transform_matrix

    # Compute M_inv = inverse(M)
    combined_matrix_inv = np.linalg.inv(combined_matrix)

    # Apply M_inv to the 4D point: result_4d = M_inv @ [u*depth, v*depth, depth, 1]^T
    result_4d = combined_matrix_inv @ point_4d

    # Divide by the homogeneous coordinate (4th element) to get [x, y, z, w] -> [x/w, y/w, z/w]
    result_3d = result_4d[:3] / result_4d[3]

    return result_3d
