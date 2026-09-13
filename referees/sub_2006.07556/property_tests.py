import numpy as np

def check(fn):
    results = []
    
    # Test 1: Kernel is symmetric in its arguments
    # Property: K(G1, G2) = K(G2, G1)
    try:
        adj1 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.int32)
        labels1 = np.array([0, 1, 0], dtype=np.int32)
        adj2 = np.array([[0, 1], [1, 0]], dtype=np.int32)
        labels2 = np.array([2, 1], dtype=np.int32)
        
        k12 = fn(adj1, labels1, adj2, labels2, h_max=2)
        k21 = fn(adj2, labels2, adj1, labels1, h_max=2)
        
        passed = abs(k12 - k21) < 1e-6
        results.append({
            "name": "Kernel symmetry",
            "passed": passed,
            "detail": f"K(G1,G2)={k12}, K(G2,G1)={k21}, diff={abs(k12-k21)}"
        })
    except Exception as e:
        results.append({
            "name": "Kernel symmetry",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Kernel is non-negative
    # Property: K(G1, G2) >= 0 (dot product of count vectors)
    try:
        adj1 = np.array([[0, 1, 1], [1, 0, 0], [1, 0, 0]], dtype=np.int32)
        labels1 = np.array([0, 1, 2], dtype=np.int32)
        adj2 = np.array([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]], dtype=np.int32)
        labels2 = np.array([1, 0, 2, 1], dtype=np.int32)
        
        k = fn(adj1, labels1, adj2, labels2, h_max=3)
        
        passed = k >= -1e-6  # Allow tiny numerical error
        results.append({
            "name": "Kernel non-negativity",
            "passed": passed,
            "detail": f"K(G1,G2)={k}"
        })
    except Exception as e:
        results.append({
            "name": "Kernel non-negativity",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Identical graphs have positive kernel
    # Property: K(G, G) > 0 for any non-empty graph
    try:
        adj = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.int32)
        labels = np.array([0, 1, 0], dtype=np.int32)
        
        k = fn(adj, labels, adj, labels, h_max=2)
        
        passed = k > 1e-6
        results.append({
            "name": "Identical graphs positive kernel",
            "passed": passed,
            "detail": f"K(G,G)={k}"
        })
    except Exception as e:
        results.append({
            "name": "Identical graphs positive kernel",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: h_max=0 gives kernel based only on initial label counts
    # Property: With h_max=0, only initial labels contribute (no iterations)
    try:
        adj1 = np.array([[0, 1], [1, 0]], dtype=np.int32)
        labels1 = np.array([5, 5], dtype=np.int32)
        adj2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.int32)
        labels2 = np.array([5, 5, 5], dtype=np.int32)
        
        k = fn(adj1, labels1, adj2, labels2, h_max=0)
        
        # Both graphs have label 5: counts are 2 and 3
        # Kernel should be 2*3 = 6
        expected = 6.0
        passed = abs(k - expected) < 1e-6
        results.append({
            "name": "h_max=0 initial labels only",
            "passed": passed,
            "detail": f"K={k}, expected={expected}, diff={abs(k-expected)}"
        })
    except Exception as e:
        results.append({
            "name": "h_max=0 initial labels only",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Disconnected node with unique label contributes independently
    # Property: An isolated node with a unique label contributes its count product
    try:
        # Graph 1: isolated node with label 99
        adj1 = np.array([[0]], dtype=np.int32)
        labels1 = np.array([99], dtype=np.int32)
        
        # Graph 2: isolated node with label 99
        adj2 = np.array([[0]], dtype=np.int32)
        labels2 = np.array([99], dtype=np.int32)
        
        k = fn(adj1, labels1, adj2, labels2, h_max=5)
        
        # Both have one node with label 99, so kernel = 1*1 = 1
        expected = 1.0
        passed = abs(k - expected) < 1e-6
        results.append({
            "name": "Isolated nodes with unique labels",
            "passed": passed,
            "detail": f"K={k}, expected={expected}, diff={abs(k-expected)}"
        })
    except Exception as e:
        results.append({
            "name": "Isolated nodes with unique labels",
            "passed": False,
            "detail": str(e)
        })
    
    return results
