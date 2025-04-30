"""
Tests for the CLI implementation of the dynamic quota mechanism.
"""

import pytest
import json
import sys
from io import StringIO
from unittest.mock import patch

from main import Country, simulate_one_period


class TestCLI:
    """
    Test suite for the CLI implementation.
    """
    
    def test_country_class(self):
        """
        Test the Country class.
        """
        country = Country("Test Country", 30)
        assert country.name == "Test Country"
        assert country.harvest_value == 30
        
        # Test proof generation
        proof = country.generate_harvest_proof(50)
        assert proof is not None
        assert "valid" in proof
        assert proof["valid"] == True  # harvest_value < quota
        
        # Test with harvest_value > quota
        country = Country("Greedy Country", 70)
        proof = country.generate_harvest_proof(50)
        assert proof["valid"] == False  # harvest_value > quota, but proof uses min()
    
    def test_simulate_one_period(self):
        """
        Test the simulate_one_period function.
        """
        countries = [
            Country("Country A", 40),
            Country("Country B", 60),
            Country("Country C", 30)
        ]
        
        results = simulate_one_period(
            countries=countries,
            current_stock=1000,
            growth_rate=0.1,
            carrying_capacity=2000,
            quota=50,
            damage_parameter=0.01
        )
        
        # Check that the results contain the expected keys
        assert "initial_stock" in results
        assert "countries" in results
        assert "total_consumption" in results
        assert "next_stock" in results
        assert "environmental_damage" in results
        assert "shadow_price" in results
        assert "proofs_verified" in results
        
        # Check that the values are correct
        assert results["initial_stock"] == 1000
        assert len(results["countries"]) == 3
        
        # Total consumption should be the sum of the actual harvests
        expected_consumption = 40 + 50 + 30  # Country B is limited by quota
        assert results["total_consumption"] == expected_consumption
        
        # Check next stock calculation
        expected_next_stock = 1000 + 0.1 * 1000 * (1 - 1000/2000) - expected_consumption
        assert results["next_stock"] == expected_next_stock
        
        # Check environmental damage
        expected_damage = 0.01 * expected_consumption**2
        assert results["environmental_damage"] == expected_damage
        
        # Check shadow price
        expected_shadow_price = 2 * 0.01 * expected_consumption
        assert results["shadow_price"] == expected_shadow_price
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_output_format(self, mock_stdout):
        """
        Test the output format of the main function.
        """
        from main import main
        
        # Mock sys.argv to simulate command-line arguments
        with patch('sys.argv', ['main.py']):
            main()
        
        # Get the output
        output = mock_stdout.getvalue()
        
        # Check that the output is valid JSON followed by a summary
        lines = output.strip().split('\n')
        json_output = '\n'.join(lines[:lines.index('')])
        
        # Parse the JSON to ensure it's valid
        try:
            results = json.loads(json_output)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
        
        # Check that the summary contains the expected information
        summary = '\n'.join(lines[lines.index(''):])
        assert "Summary:" in summary
        assert "Initial stock:" in summary
        assert "Total consumption:" in summary
        assert "Environmental damage:" in summary
        assert "Shadow price:" in summary
        assert "Next period stock:" in summary
        assert "All proofs verified:" in summary