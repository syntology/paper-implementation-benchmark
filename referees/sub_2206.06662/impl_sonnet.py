import numpy as np


def compute_candidate_cardinality(current_epoch, initial_epoch, final_epoch, initial_cardinality):
    """
    Compute the target cardinality (number of candidate combinations to retain)
    at a given epoch during the pruning schedule.
    
    This implements Eq. (card) from the LBC paper, which linearly decreases
    the number of candidates from initial_cardinality down to 1 over the
    epoch range [initial_epoch, final_epoch].
    
    Parameters:
    -----------
    current_epoch : int
        The current training epoch (1-indexed)
    initial_epoch : int
        The epoch at which pruning begins (1-indexed, inclusive)
    final_epoch : int
        The epoch at which pruning ends (1-indexed, inclusive)
    initial_cardinality : int
        The initial number of candidates at the start
    
    Returns:
    --------
    float
        The target number of candidates to retain at current_epoch
    """
    # Convert inputs to appropriate types
    current_epoch = int(current_epoch)
    initial_epoch = int(initial_epoch)
    final_epoch = int(final_epoch)
    initial_cardinality = int(initial_cardinality)
    
    # Before pruning starts, return initial cardinality
    if current_epoch < initial_epoch:
        return float(initial_cardinality)
    
    # After pruning ends, return 1
    if current_epoch >= final_epoch:
        return float(1)
    
    # Linear interpolation during pruning phase
    # cardinality = initial_cardinality - floor((current_epoch - initial_epoch) / (final_epoch - initial_epoch) * (initial_cardinality - 1))
    progress = (current_epoch - initial_epoch) / (final_epoch - initial_epoch)
    reduction = np.floor(progress * (initial_cardinality - 1))
    cardinality = initial_cardinality - reduction
    
    # Ensure result is in valid range [1, initial_cardinality]
    cardinality = max(1, min(initial_cardinality, cardinality))
    
    return float(cardinality)
