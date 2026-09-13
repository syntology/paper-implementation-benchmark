import numpy as np

def check(fn):
    results = []
    
    # Test 1: Boundary condition - before initial_epoch returns initial_cardinality
    try:
        initial_card = 10
        initial_epoch = 5
        final_epoch = 15
        
        # Test several epochs before initial_epoch
        for current_epoch in [1, 2, 4]:
            result = fn(current_epoch, initial_epoch, final_epoch, initial_card)
            assert result == initial_card, f"At epoch {current_epoch} (before initial), expected {initial_card}, got {result}"
        
        results.append({
            "name": "Boundary: before initial_epoch returns initial_cardinality",
            "passed": True,
            "detail": "All epochs before initial_epoch correctly return initial_cardinality"
        })
    except Exception as e:
        results.append({
            "name": "Boundary: before initial_epoch returns initial_cardinality",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 2: Boundary condition - at or after final_epoch returns 1
    try:
        initial_card = 10
        initial_epoch = 5
        final_epoch = 15
        
        # Test at final_epoch and beyond
        for current_epoch in [15, 16, 100]:
            result = fn(current_epoch, initial_epoch, final_epoch, initial_card)
            assert result == 1, f"At epoch {current_epoch} (>= final), expected 1, got {result}"
        
        results.append({
            "name": "Boundary: at or after final_epoch returns 1",
            "passed": True,
            "detail": "All epochs >= final_epoch correctly return 1"
        })
    except Exception as e:
        results.append({
            "name": "Boundary: at or after final_epoch returns 1",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 3: Monotonicity - cardinality is non-increasing as epoch increases
    try:
        initial_card = 20
        initial_epoch = 10
        final_epoch = 50
        
        prev_cardinality = initial_card
        for current_epoch in range(initial_epoch, final_epoch + 1):
            cardinality = fn(current_epoch, initial_epoch, final_epoch, initial_card)
            assert cardinality <= prev_cardinality, \
                f"Monotonicity violated: at epoch {current_epoch} got {cardinality}, previous was {prev_cardinality}"
            assert 1 <= cardinality <= initial_card, \
                f"Cardinality out of bounds at epoch {current_epoch}: {cardinality}"
            prev_cardinality = cardinality
        
        results.append({
            "name": "Monotonicity: cardinality non-increasing with epoch",
            "passed": True,
            "detail": "Cardinality monotonically decreases from initial_cardinality to 1"
        })
    except Exception as e:
        results.append({
            "name": "Monotonicity: cardinality non-increasing with epoch",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 4: Linear interpolation - verify exact formula at intermediate points
    try:
        initial_card = 11
        initial_epoch = 5
        final_epoch = 15
        
        # Test at initial_epoch (should be initial_cardinality)
        result = fn(initial_epoch, initial_epoch, final_epoch, initial_card)
        assert result == initial_card, f"At initial_epoch, expected {initial_card}, got {result}"
        
        # Test at midpoint
        mid_epoch = (initial_epoch + final_epoch) // 2
        expected_mid = initial_card - np.floor((mid_epoch - initial_epoch) / (final_epoch - initial_epoch) * (initial_card - 1))
        result_mid = fn(mid_epoch, initial_epoch, final_epoch, initial_card)
        assert result_mid == int(expected_mid), \
            f"At midpoint epoch {mid_epoch}, expected {int(expected_mid)}, got {result_mid}"
        
        # Test at final_epoch - 1 (should be 2 if formula is correct)
        result_penultimate = fn(final_epoch - 1, initial_epoch, final_epoch, initial_card)
        expected_penultimate = initial_card - np.floor((final_epoch - 1 - initial_epoch) / (final_epoch - initial_epoch) * (initial_card - 1))
        assert result_penultimate == int(expected_penultimate), \
            f"At epoch {final_epoch - 1}, expected {int(expected_penultimate)}, got {result_penultimate}"
        
        results.append({
            "name": "Linear interpolation: formula correctness",
            "passed": True,
            "detail": "Formula cardinality = initial - floor((epoch - init) / (final - init) * (initial - 1)) verified"
        })
    except Exception as e:
        results.append({
            "name": "Linear interpolation: formula correctness",
            "passed": False,
            "detail": str(e)
        })
    
    # Test 5: Degenerate case - single epoch range (initial_epoch == final_epoch)
    try:
        initial_card = 7
        initial_epoch = 10
        final_epoch = 10
        
        # Before the epoch
        result_before = fn(initial_epoch - 1, initial_epoch, final_epoch, initial_card)
        assert result_before == initial_card, f"Before degenerate epoch, expected {initial_card}, got {result_before}"
        
        # At the epoch (should be 1 since it's >= final_epoch)
        result_at = fn(initial_epoch, initial_epoch, final_epoch, initial_card)
        assert result_at == 1, f"At degenerate epoch, expected 1, got {result_at}"
        
        # After the epoch
        result_after = fn(initial_epoch + 1, initial_epoch, final_epoch, initial_card)
        assert result_after == 1, f"After degenerate epoch, expected 1, got {result_after}"
        
        results.append({
            "name": "Degenerate case: initial_epoch == final_epoch",
            "passed": True,
            "detail": "Degenerate case handled correctly: jumps from initial_cardinality to 1"
        })
    except Exception as e:
        results.append({
            "name": "Degenerate case: initial_epoch == final_epoch",
            "passed": False,
            "detail": str(e)
        })
    
    return results
