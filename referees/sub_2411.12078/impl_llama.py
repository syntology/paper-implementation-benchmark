import numpy as np

def fragment_score(fragment_counts, fragment_properties):
    """
    Compute scores for molecular fragments according to Eq. (score) referenced in the algorithm.

    Parameters:
    fragment_counts (array-like): A 1D array of length N where fragment_counts[i] is the occurrence count of fragment i in the dataset.
    fragment_properties (array-like): A 2D array of shape (N, P) where fragment_properties[i, j] is the j-th property value of fragment i.

    Returns:
    scores (numpy.ndarray): A 1D array of length N containing the score for each fragment.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    fragment_counts = np.asarray(fragment_counts, dtype=float)
    fragment_properties = np.asarray(fragment_properties, dtype=float)

    # Compute mean of properties for each fragment
    # If a fragment has zero properties (P=0), treat mean as 1.0
    mean_properties = np.mean(fragment_properties, axis=1, where=fragment_properties.shape[1] > 0)
    mean_properties = np.where(np.isnan(mean_properties), 1.0, mean_properties)

    # Compute scores by multiplying fragment counts with mean properties
    scores = fragment_counts * mean_properties

    return scores
