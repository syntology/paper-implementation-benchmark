import numpy as np

def compute_typicality(embeddings, cluster_assignments, point_index):
    """
    Compute the typicality score for a single point within its assigned cluster.

    Parameters:
    embeddings (array-like): (N, D) array of embeddings where N is the number of points and D is the embedding dimension.
    cluster_assignments (array-like): length-N array of cluster labels (0-indexed).
    point_index (int): 0-indexed integer in range [0, N-1].

    Returns:
    float: Typicality score of the point at point_index.
    """
    embeddings = np.asarray(embeddings, dtype=float)
    cluster_assignments = np.asarray(cluster_assignments, dtype=int)

    # Step 1: Identify the cluster label c = cluster_assignments[point_index]
    cluster_label = cluster_assignments[point_index]

    # Step 2: Find all points in cluster c: mask = (cluster_assignments == c)
    mask = (cluster_assignments == cluster_label)

    # Step 3: Compute the centroid of cluster c as the mean of embeddings[mask] along axis 0
    centroid = np.mean(embeddings[mask], axis=0)

    # Step 4: Compute the Euclidean distance d between embeddings[point_index] and the centroid
    distance = np.sqrt(np.sum((embeddings[point_index] - centroid) ** 2))

    # Step 5: Return -d (negative distance)
    return -distance
