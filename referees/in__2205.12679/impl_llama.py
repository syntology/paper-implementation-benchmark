import numpy as np

def compute_meta_gradient_for_sample_weights(val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w):
    """
    Compute the meta-gradient of the robust loss with respect to sample weights using implicit differentiation.

    Parameters:
    val_loss_grad_theta (array-like): Gradient of validation loss w.r.t. model parameters theta, shape (D,)
    train_loss_hessian_theta (array-like): Hessian of the weighted training loss w.r.t. theta, shape (D, D)
    train_loss_grad_theta_grad_w (array-like): Mixed partial derivatives of training loss w.r.t. both theta and sample weights w, shape (D, N)

    Returns:
    meta_gradient (numpy array): A 1D numpy array of shape (N,) with the gradient w.r.t. each sample weight
    """
    # Convert array-like arguments to numpy arrays with float dtype
    val_loss_grad_theta = np.asarray(val_loss_grad_theta, dtype=float)
    train_loss_hessian_theta = np.asarray(train_loss_hessian_theta, dtype=float)
    train_loss_grad_theta_grad_w = np.asarray(train_loss_grad_theta_grad_w, dtype=float)

    # Compute the inverse of train_loss_hessian_theta @ x = val_loss_grad_theta for x using numpy.linalg.solve
    x = np.linalg.solve(train_loss_hessian_theta, val_loss_grad_theta)

    # Compute the meta-gradient as -x^T @ train_loss_grad_theta_grad_w
    meta_gradient = -np.dot(x, train_loss_grad_theta_grad_w)

    return meta_gradient
