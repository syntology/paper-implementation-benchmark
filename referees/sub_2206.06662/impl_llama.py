import numpy as np

def compute_candidate_cardinality(current_epoch, initial_epoch, final_epoch, initial_cardinality):
    """
    Compute the target cardinality (number of candidate combinations to retain) at a given epoch during the pruning schedule.

    Parameters:
    current_epoch (int): the current training epoch (1-indexed)
    initial_epoch (int): the epoch at which pruning begins (1-indexed, inclusive)
    final_epoch (int): the epoch at which pruning ends (1-indexed, inclusive)
    initial_cardinality (int): the initial number of candidates at the start

    Returns:
    int: the target number of candidates to retain at current_epoch
    """
    current_epoch = np.asarray(current_epoch, dtype=float)
    initial_epoch = np.asarray(initial_epoch, dtype=float)
    final_epoch = np.asarray(final_epoch, dtype=float)
    initial_cardinality = np.asarray(initial_cardinality, dtype=float)

    if current_epoch < initial_epoch:
        return int(initial_cardinality)
    elif current_epoch >= final_epoch:
        return 1
    else:
        cardinality = initial_cardinality - np.floor((current_epoch - initial_epoch) / (final_epoch - initial_epoch) * (initial_cardinality - 1))
        return int(cardinality)
