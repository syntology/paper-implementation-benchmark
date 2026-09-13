import numpy as np


def compute_meta_gradient_for_sample_weights(
    val_loss_grad_theta, train_loss_hessian_theta, train_loss_grad_theta_grad_w
):
    """
    Compute the meta-gradient of the robust loss with respect to sample weights
    using implicit differentiation (Equation 3 from SUNGEN paper).
    
    The meta-gradient is computed as:
    -val_loss_grad_theta^T @ inv(train_loss_hessian_theta) @ train_loss_grad_theta_grad_w
    
    Args:
        val_loss_grad_theta: Gradient of validation loss w.r.t. model parameters theta.
                            Shape (D,) where D is the number of parameters.
        train_loss_hessian_theta: Hessian of the weighted training loss w.r.t. theta.
                                 Shape (D, D).
        train_loss_grad_theta_grad_w: Mixed partial derivatives of training loss w.r.t.
                                     both theta and sample weights w. Shape (D, N) where
                                     N is the number of training samples and entry [i,j]
                                     is d²L/(dθ_i dw_j).
    
    Returns:
        meta_gradient: 1D numpy array of shape (N,) representing the gradient w.r.t.
                      each sample weight.
    """
    # Convert inputs to numpy arrays with float dtype
    val_loss_grad_theta = np.asarray(val_loss_grad_theta, dtype=float)
    train_loss_hessian_theta = np.asarray(train_loss_hessian_theta, dtype=float)
    train_loss_grad_theta_grad_w = np.asarray(train_loss_grad_theta_grad_w, dtype=float)
    
    # Solve train_loss_hessian_theta @ x = val_loss_grad_theta for x
    # This is equivalent to computing inv(train_loss_hessian_theta) @ val_loss_grad_theta
    # but more numerically stable and efficient
    x = np.linalg.solve(train_loss_hessian_theta, val_loss_grad_theta)
    
    # Compute -x^T @ train_loss_grad_theta_grad_w
    meta_gradient = -x @ train_loss_grad_theta_grad_w
    
    return meta_gradient
