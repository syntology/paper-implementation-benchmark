import numpy as np


def unproject_2d_point_with_depth(point_2d, depth, projection_matrix, transform_matrix):
    """
    Unproject a 2D image point to 3D space using a given depth value.
    
    Args:
        point_2d: Length-2 array [u, v] in pixel coordinates (0-indexed)
        depth: Scalar float representing the distance along the ray
        projection_matrix: 4x4 camera projection matrix P_rgb
        transform_matrix: 4x4 transformation matrix T from lidar to camera coordinates
    
    Returns:
        Length-3 array [x, y, z] representing the 3D point in lidar coordinate frame
    """
    # Convert inputs to numpy arrays
    point_2d = np.asarray(point_2d, dtype=float)
    depth = float(depth)
    projection_matrix = np.asarray(projection_matrix, dtype=float)
    transform_matrix = np.asarray(transform_matrix, dtype=float)
    
    # Step 1-2: Create homogeneous 2D point and multiply by depth
    u, v = point_2d[0], point_2d[1]
    
    # Step 3: Create 4D homogeneous point [u*depth, v*depth, depth, 1]
    point_4d = np.array([u * depth, v * depth, depth, 1.0], dtype=float)
    
    # Step 4: Compute the combined transformation matrix M = P_rgb @ T
    M = projection_matrix @ transform_matrix
    
    # Step 5: Compute inverse of M
    M_inv = np.linalg.inv(M)
    
    # Step 6: Apply M_inv to the 4D point
    result_4d = M_inv @ point_4d
    
    # Step 7: Divide by the homogeneous coordinate (4th element)
    w = result_4d[3]
    result_3d = result_4d[:3] / w
    
    # Step 8: Return the first 3 elements as a length-3 array
    return result_3d
