import pytest
import numpy as np
from pytest import approx
import sys
import os

# Add the project directory to the path so we can import the mechanism module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the mechanism module (will be created later)
try:
    from mechanism import (
        logistic_growth,
        enforce_quota,
        compute_damage,
        compute_shadow_price,
        ZKProof
    )
except ImportError:
    # Define placeholder functions for the first run when mechanism.py doesn't exist yet
    def logistic_growth(*args, **kwargs):
        return 0
    
    def enforce_quota(*args, **kwargs):
        return False
    
    def compute_damage(*args, **kwargs):
        return 0
    
    def compute_shadow_price(*args, **kwargs):
        return 0
    
    class ZKProof:
        def generate_proof(self, *args, **kwargs):
            return None
        
        def verify_proof(self, *args, **kwargs):
            return False


class TestMechanism:
    """
    Test suite for the dynamic quota mechanism based on Harrison & Lagunoff (2016).
    """
    
    def test_logistic_growth(self):
        """
        Test that logistic_growth(S, r, K, C) == S + r*S*(1 - S/K) - C
        """
        # Test with various parameter values
        assert logistic_growth(100, 0.1, 1000, 5) == approx(100 + 0.1*100*(1 - 100/1000) - 5)
        assert logistic_growth(500, 0.2, 1000, 20) == approx(500 + 0.2*500*(1 - 500/1000) - 20)
        assert logistic_growth(0, 0.3, 500, 0) == approx(0)  # No growth from zero stock
        assert logistic_growth(1000, 0.1, 1000, 10) == approx(1000 - 10)  # At carrying capacity
    
    def test_enforce_quota(self):
        """
        Test that enforce_quota(h_i, Q) raises if h_i > Q, passes if h_i <= Q
        """
        # Test when harvest is within quota
        assert enforce_quota(5, 10) == True
        assert enforce_quota(10, 10) == True
        
        # Test when harvest exceeds quota
        with pytest.raises(ValueError, match="Harvest exceeds quota"):
            enforce_quota(15, 10)
    
    def test_compute_damage(self):
        """
        Test that compute_damage(C, δ) returns δ * C**2
        """
        assert compute_damage(10, 0.1) == approx(0.1 * 10**2)
        assert compute_damage(5, 0.2) == approx(0.2 * 5**2)
        assert compute_damage(0, 0.3) == approx(0)
    
    def test_compute_shadow_price(self):
        """
        Test that compute_shadow_price(C, δ) returns 2*δ*C
        """
        assert compute_shadow_price(10, 0.1) == approx(2 * 0.1 * 10)
        assert compute_shadow_price(5, 0.2) == approx(2 * 0.2 * 5)
        assert compute_shadow_price(0, 0.3) == approx(0)
    
    def test_zkp_verification(self):
        """
        Test that a ZKP proof object verifies h_i <= Q without revealing h_i
        """
        # Create a ZKP proof for a valid harvest (h_i <= Q)
        zkp = ZKProof()
        h_i = 8
        Q = 10
        proof = zkp.generate_proof(h_i, Q)
        
        # Verify the proof without knowing h_i
        assert zkp.verify_proof(proof, Q) == True
        
        # Create a ZKP proof for an invalid harvest (h_i > Q)
        h_i = 12
        Q = 10
        proof = zkp.generate_proof(h_i, Q)
        
        # Verify the proof should fail
        assert zkp.verify_proof(proof, Q) == False