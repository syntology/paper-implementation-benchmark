import numpy as np

def entk_predict(K_test_train, K_train_train, Y_train):
    """
    Compute empirical Neural Tangent Kernel (eNTK) predictions for test examples given a subset of training data.

    Parameters:
    K_test_train (array-like): 2D array of shape (n_test, n_train_subset) containing kernel values between test points and the training subset.
    K_train_train (array-like): 2D array of shape (n_train_subset, n_train_subset) containing kernel values among the training subset points.
    Y_train (array-like): 1D array of shape (n_train_subset,) containing labels for the training subset.

    Returns:
    array: 1D array of shape (n_test,) containing the predicted values for test examples.
    """
    # Convert array-like arguments to numpy arrays with float dtype
    K_test_train = np.asarray(K_test_train, dtype=float)
    K_train_train = np.asarray(K_train_train, dtype=float)
    Y_train = np.asarray(Y_train, dtype=float)

    # Compute the inverse of K_train_train
    K_train_train_inv = np.linalg.inv(K_train_train)

    # Compute the eNTK predictions
    predictions = np.dot(np.dot(K_test_train, K_train_train_inv), Y_train)

    return predictions
