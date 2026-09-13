import numpy as np


def compute_replan_probability(epsilon, q_old, q_new):
    """
    Compute the categorical probability of replanning (selecting the new plan).
    
    According to the GPM algorithm, m ~ Categorical([epsilon, Q(s, tau_new) - Q(s, tau_old)]).
    This is interpreted as a 2-category distribution where:
    - Category 0 (m=0): keep old plan, logit = epsilon
    - Category 1 (m=1): select new plan, logit = q_new - q_old
    
    We apply softmax normalization and return the probability of category 1.
    
    Args:
        epsilon: Scalar replan threshold parameter
        q_old: Scalar Q-value of the old plan
        q_new: Scalar Q-value of the new plan
    
    Returns:
        Probability of selecting the new plan (m=1) as a Python float
    """
    # Convert inputs to numpy arrays and ensure float type
    epsilon = np.asarray(epsilon, dtype=float)
    q_old = np.asarray(q_old, dtype=float)
    q_new = np.asarray(q_new, dtype=float)
    
    # Compute logits for the categorical distribution
    # logit[0] = epsilon (for keeping old plan, m=0)
    # logit[1] = q_new - q_old (for selecting new plan, m=1)
    logit_0 = epsilon
    logit_1 = q_new - q_old
    
    # Apply softmax with log-sum-exp trick for numerical stability
    # Subtract max logit before exponentiating
    max_logit = np.maximum(logit_0, logit_1)
    
    exp_logit_0 = np.exp(logit_0 - max_logit)
    exp_logit_1 = np.exp(logit_1 - max_logit)
    
    sum_exp = exp_logit_0 + exp_logit_1
    
    # Probability of category 1 (selecting new plan)
    prob_new_plan = exp_logit_1 / sum_exp
    
    # Convert to Python float scalar
    return float(prob_new_plan)
