import numpy as np

def weisfeiler_lehman_kernel(adj_matrix_1, node_labels_1, adj_matrix_2, node_labels_2, h_max):
    """
    Compute the Weisfeiler-Lehman subtree kernel between two graphs.
    
    Parameters:
    -----------
    adj_matrix_1 : array-like, shape (n1, n1)
        Adjacency matrix of the first graph
    node_labels_1 : array-like, shape (n1,)
        Initial node labels of the first graph
    adj_matrix_2 : array-like, shape (n2, n2)
        Adjacency matrix of the second graph
    node_labels_2 : array-like, shape (n2,)
        Initial node labels of the second graph
    h_max : int
        Maximum number of WL iterations
    
    Returns:
    --------
    float
        The kernel value between the two graphs
    """
    # Convert inputs to numpy arrays
    adj_matrix_1 = np.asarray(adj_matrix_1, dtype=float)
    node_labels_1 = np.asarray(node_labels_1, dtype=float)
    adj_matrix_2 = np.asarray(adj_matrix_2, dtype=float)
    node_labels_2 = np.asarray(node_labels_2, dtype=float)
    
    # Convert node labels to integers
    labels_1 = node_labels_1.astype(int).copy()
    labels_2 = node_labels_2.astype(int).copy()
    
    # Initialize feature vectors with counts of original node labels (h=0)
    phi_1 = _count_labels(labels_1)
    phi_2 = _count_labels(labels_2)
    
    # Perform WL iterations
    for h in range(1, h_max + 1):
        # Update labels for graph 1
        labels_1 = _wl_iteration(adj_matrix_1, labels_1)
        # Update labels for graph 2
        labels_2 = _wl_iteration(adj_matrix_2, labels_2)
        
        # Accumulate new label counts to feature vectors
        new_counts_1 = _count_labels(labels_1)
        new_counts_2 = _count_labels(labels_2)
        
        for label, count in new_counts_1.items():
            phi_1[label] = phi_1.get(label, 0) + count
        
        for label, count in new_counts_2.items():
            phi_2[label] = phi_2.get(label, 0) + count
    
    # Compute kernel as dot product of feature vectors
    kernel_value = _dot_product(phi_1, phi_2)
    
    return float(kernel_value)


def _count_labels(labels):
    """Count occurrences of each unique label."""
    counts = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return counts


def _wl_iteration(adj_matrix, labels):
    """Perform one WL iteration to compute new node labels."""
    n = len(labels)
    new_labels = np.zeros(n, dtype=int)
    
    for v in range(n):
        # Collect neighbor labels (multiset)
        neighbor_labels = []
        for u in range(n):
            if adj_matrix[v, u] == 1:
                neighbor_labels.append(labels[u])
        
        # Sort neighbor labels in ascending order
        neighbor_labels.sort()
        
        # Prepend current node label
        label_list = [labels[v]] + neighbor_labels
        
        # Convert to string representation
        label_string = ','.join(str(label) for label in label_list)
        
        # Hash the string and take modulo 2^31 for non-negative integer
        hashed_label = hash(label_string) % (2**31)
        
        new_labels[v] = hashed_label
    
    return new_labels


def _dot_product(phi_1, phi_2):
    """Compute dot product between two feature dictionaries."""
    dot_prod = 0
    
    # Sum over all labels in both dictionaries
    all_labels = set(phi_1.keys()) | set(phi_2.keys())
    
    for label in all_labels:
        count_1 = phi_1.get(label, 0)
        count_2 = phi_2.get(label, 0)
        dot_prod += count_1 * count_2
    
    return dot_prod
