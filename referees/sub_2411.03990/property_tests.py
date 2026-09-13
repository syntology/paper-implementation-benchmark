import numpy as np
from scipy.linalg import logm, expm

def check(fn):
    results = []
    
    # Test 1: Identity input produces identity output
    # When H_k = I and H_hat_k_to_0 = I, M_i = I, log(I) = 0, so combined = 0, exp(0) = I
    def test_identity_input():
        try:
            T_p = 2
            H_k = np.array([np.eye(4) for _ in range(T_p + 1)])
            H_hat_k_to_0 = np.array([np.eye(4) for _ in range(T_p + 1)])
            lambda_0, lambda_1 = 0.5, 0.5
            
            result = fn(H_k, H_hat_k_to_0, lambda_0, lambda_1)
            
            # Result should be identity matrices
            for i in range(T_p + 1):
                if not np.allclose(result[i], np.eye(4), atol=1e-6):
                    return False, f"Index {i}: expected identity, got {result[i]}"
            return True, "Identity input produces identity output"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_identity_input()
    results.append({"name": "test_identity_input", "passed": passed, "detail": detail})
    
    # Test 2: Output matrices are valid SE(3) (bottom row is [0,0,0,1])
    # All output matrices must have the SE(3) structure
    def test_output_se3_structure():
        try:
            np.random.seed(42)
            T_p = 3
            
            # Create random valid SE(3) matrices
            H_k = np.array([np.eye(4) for _ in range(T_p + 1)])
            H_hat_k_to_0 = np.array([np.eye(4) for _ in range(T_p + 1)])
            
            for i in range(T_p + 1):
                # Random rotation (via QR decomposition)
                Q, _ = np.linalg.qr(np.random.randn(3, 3))
                # Ensure det = 1 (proper rotation)
                if np.linalg.det(Q) < 0:
                    Q = -Q
                H_k[i, :3, :3] = Q
                H_k[i, :3, 3] = np.random.randn(3)
                
                H_hat_k_to_0[i, :3, :3] = Q
                H_hat_k_to_0[i, :3, 3] = np.random.randn(3)
            
            lambda_0, lambda_1 = 0.3, 0.7
            result = fn(H_k, H_hat_k_to_0, lambda_0, lambda_1)
            
            # Check all output matrices have SE(3) structure
            for i in range(T_p + 1):
                bottom_row = result[i, 3, :]
                expected_bottom = np.array([0, 0, 0, 1])
                if not np.allclose(bottom_row, expected_bottom, atol=1e-6):
                    return False, f"Index {i}: bottom row is {bottom_row}, expected {expected_bottom}"
            
            return True, "All output matrices have valid SE(3) structure"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_output_se3_structure()
    results.append({"name": "test_output_se3_structure", "passed": passed, "detail": detail})
    
    # Test 3: Lambda weighting property - when lambda_1 = 0, result depends only on H_hat_k_to_0
    # When lambda_1 = 0: combined = lambda_0 * log(H_hat @ H_k^-1)
    def test_lambda_weighting():
        try:
            np.random.seed(43)
            T_p = 2
            
            # Create valid SE(3) matrices
            H_k = np.array([np.eye(4) for _ in range(T_p + 1)])
            H_hat_k_to_0 = np.array([np.eye(4) for _ in range(T_p + 1)])
            
            for i in range(T_p + 1):
                Q, _ = np.linalg.qr(np.random.randn(3, 3))
                if np.linalg.det(Q) < 0:
                    Q = -Q
                H_k[i, :3, :3] = Q
                H_k[i, :3, 3] = np.random.randn(3) * 0.1
                
                Q2, _ = np.linalg.qr(np.random.randn(3, 3))
                if np.linalg.det(Q2) < 0:
                    Q2 = -Q2
                H_hat_k_to_0[i, :3, :3] = Q2
                H_hat_k_to_0[i, :3, 3] = np.random.randn(3) * 0.1
            
            # Test with lambda_1 = 0
            lambda_0 = 0.5
            result_lambda1_zero = fn(H_k, H_hat_k_to_0, lambda_0, 0.0)
            
            # Test with different lambda_0 but same ratio
            result_lambda1_zero_2 = fn(H_k, H_hat_k_to_0, lambda_0 * 2, 0.0)
            
            # Results should differ (scaling effect of lambda_0)
            # but both should be valid SE(3)
            for i in range(T_p + 1):
                if not np.allclose(result_lambda1_zero[i, 3, :], [0, 0, 0, 1], atol=1e-6):
                    return False, f"Result 1 index {i} not SE(3)"
                if not np.allclose(result_lambda1_zero_2[i, 3, :], [0, 0, 0, 1], atol=1e-6):
                    return False, f"Result 2 index {i} not SE(3)"
            
            return True, "Lambda weighting produces valid SE(3) outputs"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_lambda_weighting()
    results.append({"name": "test_lambda_weighting", "passed": passed, "detail": detail})
    
    # Test 4: Output shape matches input shape
    def test_output_shape():
        try:
            np.random.seed(44)
            for T_p in [1, 3, 5]:
                H_k = np.array([np.eye(4) for _ in range(T_p + 1)])
                H_hat_k_to_0 = np.array([np.eye(4) for _ in range(T_p + 1)])
                
                for i in range(T_p + 1):
                    Q, _ = np.linalg.qr(np.random.randn(3, 3))
                    if np.linalg.det(Q) < 0:
                        Q = -Q
                    H_k[i, :3, :3] = Q
                    H_k[i, :3, 3] = np.random.randn(3) * 0.05
                    
                    Q2, _ = np.linalg.qr(np.random.randn(3, 3))
                    if np.linalg.det(Q2) < 0:
                        Q2 = -Q2
                    H_hat_k_to_0[i, :3, :3] = Q2
                    H_hat_k_to_0[i, :3, 3] = np.random.randn(3) * 0.05
                
                result = fn(H_k, H_hat_k_to_0, 0.5, 0.5)
                
                if result.shape != (T_p + 1, 4, 4):
                    return False, f"T_p={T_p}: expected shape {(T_p + 1, 4, 4)}, got {result.shape}"
            
            return True, "Output shape matches input shape for all T_p"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_output_shape()
    results.append({"name": "test_output_shape", "passed": passed, "detail": detail})
    
    # Test 5: Rotation matrices in output have determinant ≈ 1 (proper rotations)
    def test_output_rotation_determinant():
        try:
            np.random.seed(45)
            T_p = 2
            
            H_k = np.array([np.eye(4) for _ in range(T_p + 1)])
            H_hat_k_to_0 = np.array([np.eye(4) for _ in range(T_p + 1)])
            
            for i in range(T_p + 1):
                Q, _ = np.linalg.qr(np.random.randn(3, 3))
                if np.linalg.det(Q) < 0:
                    Q = -Q
                H_k[i, :3, :3] = Q
                H_k[i, :3, 3] = np.random.randn(3) * 0.05
                
                Q2, _ = np.linalg.qr(np.random.randn(3, 3))
                if np.linalg.det(Q2) < 0:
                    Q2 = -Q2
                H_hat_k_to_0[i, :3, :3] = Q2
                H_hat_k_to_0[i, :3, 3] = np.random.randn(3) * 0.05
            
            result = fn(H_k, H_hat_k_to_0, 0.4, 0.6)
            
            for i in range(T_p + 1):
                R = result[i, :3, :3]
                det_R = np.linalg.det(R)
                if not np.isclose(det_R, 1.0, atol=1e-5):
                    return False, f"Index {i}: rotation determinant is {det_R}, expected ≈ 1.0"
            
            return True, "All output rotation matrices have determinant ≈ 1"
        except Exception as e:
            return False, str(e)
    
    passed, detail = test_output_rotation_determinant()
    results.append({"name": "test_output_rotation_determinant", "passed": passed, "detail": detail})
    
    return results
