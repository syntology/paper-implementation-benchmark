import numpy as np


def entk_predict(K_test_train, K_train_train, Y_train):
    """
    Compute empirical Neural Tangent Kernel (eNTK) predictions for test examples.
    
    This implements the prediction step from the FreeShap algorithm:
    f_{S}^{entk}(D_T) = K[T,S] @ K[S,S]^{-1} @ Y_S
    
    Args:
        K_test_train: 2D array of shape (n_test, n_train_subset) containing 
                      kernel values between test points and training subset
        K_train_train: 2D array of shape (n_train_subset, n_train_subset) 
                       containing kernel values among training subset points
        Y_train: 1D array of shape (n_train_subset,) containing labels for 
                 the training subset
    
    Returns:
        1D array of shape (n_test,) containing predicted values for test examples
    """
    # Convert inputs to numpy arrays with float dtype
    K_test_train = np.asarray(K_test_train, dtype=float)
    K_train_train = np.asarray(K_train_train, dtype=float)
    Y_train = np.asarray(Y_train, dtype=float)
    
    # Compute K[S,S]^{-1}
    K_train_train_inv = np.linalg.inv(K_train_train)
    
    # Compute K[T,S] @ K[S,S]^{-1} @ Y_S
    predictions = K_test_train @ K_train_train_inv @ Y_train
    
    return predictions
