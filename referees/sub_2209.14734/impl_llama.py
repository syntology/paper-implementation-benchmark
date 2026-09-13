import numpy as np

def compute_guidance_gradient(g_t, y_hat, y_target, lambda_scale):
    """
    Compute the gradient of the guidance term for discrete graph diffusion.

    Parameters:
    g_t (array-like): Graph state, shape [n, n] adjacency matrix with integer edge types 0..k-1
    y_hat (array-like): Predicted property, shape [d] float vector
    y_target (array-like): Target property, shape [d] float vector
    lambda_scale (float): Guidance scale

    Returns:
    float array: Scaled gradient matrix of shape [n, n]
    """
    g_t = np.asarray(g_t, dtype=float)
    y_hat = np.asarray(y_hat, dtype=float)
    y_target = np.asarray(y_target, dtype=float)
    lambda_scale = float(lambda_scale)

    def loss(g_t, y_hat, y_target):
        """
        Compute the L2 norm of the difference between y_hat and y_target.

        Parameters:
        g_t (array-like): Graph state, shape [n, n] adjacency matrix with integer edge types 0..k-1
        y_hat (array-like): Predicted property, shape [d] float vector
        y_target (array-like): Target property, shape [d] float vector

        Returns:
        float: L2 norm of the difference between y_hat and y_target
        """
        return np.sum((y_hat - y_target) ** 2)

    def perturb_g_t(g_t, i, j):
        """
        Perturb the graph state g_t by incrementing the entry at position (i, j).

        Parameters:
        g_t (array-like): Graph state, shape [n, n] adjacency matrix with integer edge types 0..k-1
        i (int): Row index
        j (int): Column index

        Returns:
        array-like: Perturbed graph state
        """
        g_t_perturbed = g_t.copy()
        if g_t_perturbed[i, j] < 2:  # assume max=2 for edge types 0,1,2
            g_t_perturbed[i, j] += 1
        return g_t_perturbed

    def compute_gradient_entry(g_t, y_hat, y_target, i, j):
        """
        Compute the gradient entry at position (i, j) using forward finite difference.

        Parameters:
        g_t (array-like): Graph state, shape [n, n] adjacency matrix with integer edge types 0..k-1
        y_hat (array-like): Predicted property, shape [d] float vector
        y_target (array-like): Target property, shape [d] float vector
        i (int): Row index
        j (int): Column index

        Returns:
        float: Gradient entry at position (i, j)
        """
        g_t_perturbed = perturb_g_t(g_t, i, j)
        y_hat_perturbed = y_hat  # assume y_hat is constant
        return loss(g_t_perturbed, y_hat_perturbed, y_target) - loss(g_t, y_hat, y_target)

    n = g_t.shape[0]
    gradient_matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if g_t[i, j] < 2:  # assume max=2 for edge types 0,1,2
                gradient_matrix[i, j] = compute_gradient_entry(g_t, y_hat, y_target, i, j)
    return lambda_scale * gradient_matrix
