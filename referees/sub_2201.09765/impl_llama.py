import numpy as np

def log_sum_exp(logits):
    """
    Compute the log sum exp of a list of logits.
    
    Parameters:
    logits (numpy array): The input logits.
    
    Returns:
    float: The log sum exp of the input logits.
    """
    max_logit = np.max(logits)
    return max_logit + np.log(np.sum(np.exp(logits - max_logit)))

def compute_replan_probability(epsilon, q_old, q_new):
    """
    Compute the categorical probability of replanning.
    
    Parameters:
    epsilon (float): The replan threshold.
    q_old (float): The Q-value of the old plan.
    q_new (float): The Q-value of the new plan.
    
    Returns:
    float: The probability of selecting the new plan.
    """
    epsilon = np.asarray(epsilon, dtype=float)
    q_old = np.asarray(q_old, dtype=float)
    q_new = np.asarray(q_new, dtype=float)
    
    logits = np.array([epsilon, q_new - q_old])
    log_sum_exp_value = log_sum_exp(logits)
    probability = np.exp(logits[1] - log_sum_exp_value)
    return float(probability)
