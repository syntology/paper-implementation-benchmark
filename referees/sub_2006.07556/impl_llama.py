import numpy as np

def weisfeiler_lehman_kernel(adj_matrix_1, node_labels_1, adj_matrix_2, node_labels_2, h_max):
    """
    Compute the Weisfeiler-Lehman subtree kernel between two graphs.

    Parameters:
    adj_matrix_1 (numpy array): Adjacency matrix of the first graph.
    node_labels_1 (numpy array): Initial node labels of the first graph.
    adj_matrix_2 (numpy array): Adjacency matrix of the second graph.
    node_labels_2 (numpy array): Initial node labels of the second graph.
    h_max (int): Maximum number of WL iterations.

    Returns:
    float: The kernel value between the two graphs.
    """
    adj_matrix_1 = np.asarray(adj_matrix_1, dtype=float)
    node_labels_1 = np.asarray(node_labels_1, dtype=float)
    adj_matrix_2 = np.asarray(adj_matrix_2, dtype=float)
    node_labels_2 = np.asarray(node_labels_2, dtype=float)

    def initialize_feature_vector(node_labels):
        """
        Initialize the feature vector as a dictionary mapping each unique label to its count.

        Parameters:
        node_labels (numpy array): Node labels.

        Returns:
        dict: The feature vector.
        """
        feature_vector = {}
        for label in np.unique(node_labels):
            feature_vector[int(label)] = np.sum(node_labels == label)
        return feature_vector

    def update_node_labels(adj_matrix, node_labels, h):
        """
        Update the node labels using the Weisfeiler-Lehman kernel.

        Parameters:
        adj_matrix (numpy array): Adjacency matrix.
        node_labels (numpy array): Current node labels.
        h (int): Current iteration.

        Returns:
        numpy array: The updated node labels.
        """
        new_labels = []
        for v in range(len(node_labels)):
            neighbors = np.where(adj_matrix[v] == 1)[0]
            neighbor_labels = node_labels[neighbors]
            sorted_labels = np.sort(neighbor_labels)
            label_string = str(int(node_labels[v])) + ',' + ','.join(map(str, sorted_labels))
            new_label = hash(label_string) % (2**31)
            new_labels.append(new_label)
        return np.array(new_labels)

    def update_feature_vector(feature_vector, node_labels):
        """
        Update the feature vector with the new node labels.

        Parameters:
        feature_vector (dict): The current feature vector.
        node_labels (numpy array): The new node labels.

        Returns:
        dict: The updated feature vector.
        """
        for label in np.unique(node_labels):
            if int(label) in feature_vector:
                feature_vector[int(label)] += np.sum(node_labels == label)
            else:
                feature_vector[int(label)] = np.sum(node_labels == label)
        return feature_vector

    phi_1 = initialize_feature_vector(node_labels_1)
    phi_2 = initialize_feature_vector(node_labels_2)

    for h in range(1, h_max + 1):
        node_labels_1 = update_node_labels(adj_matrix_1, node_labels_1, h)
        node_labels_2 = update_node_labels(adj_matrix_2, node_labels_2, h)
        phi_1 = update_feature_vector(phi_1, node_labels_1)
        phi_2 = update_feature_vector(phi_2, node_labels_2)

    kernel_value = 0.0
    all_labels = set(list(phi_1.keys()) + list(phi_2.keys()))
    for label in all_labels:
        count_1 = phi_1.get(label, 0)
        count_2 = phi_2.get(label, 0)
        kernel_value += count_1 * count_2

    return float(kernel_value)
