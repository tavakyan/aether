#!/usr/bin/env python3
"""
CLI for the Dynamic Quota Mechanism

This script provides a command-line interface to simulate the dynamic quota mechanism
from Harrison & Lagunoff (2016) "Dynamic Mechanism Design for a Global Commons".
"""

import argparse
import json
from typing import Dict, List, Any
import numpy as np

from mechanism import (
    logistic_growth,
    enforce_quota,
    compute_damage,
    compute_shadow_price,
    ZKProof
)


class Country:
    """
    Represents a country in the global commons model.
    """
    
    def __init__(self, name: str, harvest_value: float):
        """
        Initialize a country.
        
        Args:
            name: Name of the country
            harvest_value: The country's private value for harvesting
        """
        self.name = name
        self.harvest_value = harvest_value
        self.zkp = ZKProof()
    
    def generate_harvest_proof(self, quota: float) -> Dict[str, Any]:
        """
        Generate a proof that the country's harvest is within its quota.
        
        Args:
            quota: The quota allocated to the country
            
        Returns:
            A ZKP proof object
        """
        # In a real implementation, the country would choose its optimal harvest
        # based on its private value and the quota constraint
        # For the test, we'll use the harvest_value directly to check if it exceeds quota
        
        return self.zkp.generate_proof(self.harvest_value, quota)


def simulate_one_period(
    countries: List[Country],
    current_stock: float,
    growth_rate: float,
    carrying_capacity: float,
    quota: float,
    damage_parameter: float
) -> Dict[str, Any]:
    """
    Simulate one period of the dynamic quota mechanism.
    
    Args:
        countries: List of countries
        current_stock: Current resource stock
        growth_rate: Intrinsic growth rate
        carrying_capacity: Carrying capacity
        quota: Quota per country
        damage_parameter: Damage parameter
        
    Returns:
        Dictionary with simulation results
    """
    results = {
        "initial_stock": current_stock,
        "countries": [],
        "total_consumption": 0,
        "proofs_verified": True
    }
    
    # Generate proofs for each country
    total_consumption = 0
    for country in countries:
        proof = country.generate_harvest_proof(quota)
        
        # Verify the proof
        is_valid = country.zkp.verify_proof(proof, quota)
        
        # If any proof is invalid, the whole verification fails
        if not is_valid:
            results["proofs_verified"] = False
            
        # For simplicity, we'll assume countries comply with the quota
        # even if their proof is invalid (in a real system, there would be enforcement)
        actual_harvest = min(country.harvest_value, quota)
        total_consumption += actual_harvest
        
        # Add country results
        results["countries"].append({
            "name": country.name,
            "proof_valid": is_valid,
            "actual_harvest": actual_harvest,
            "desired_harvest": country.harvest_value
        })
    
    # Calculate total consumption and next period's stock
    results["total_consumption"] = total_consumption
    results["next_stock"] = logistic_growth(
        current_stock, growth_rate, carrying_capacity, total_consumption
    )
    
    # Calculate environmental damage and shadow price
    results["environmental_damage"] = compute_damage(total_consumption, damage_parameter)
    results["shadow_price"] = compute_shadow_price(total_consumption, damage_parameter)
    
    return results


def main():
    """
    Main function to run the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Simulate the dynamic quota mechanism for a global commons"
    )
    parser.add_argument(
        "--stock", type=float, default=1000,
        help="Initial resource stock (default: 1000)"
    )
    parser.add_argument(
        "--growth-rate", type=float, default=0.1,
        help="Intrinsic growth rate (default: 0.1)"
    )
    parser.add_argument(
        "--carrying-capacity", type=float, default=2000,
        help="Carrying capacity (default: 2000)"
    )
    parser.add_argument(
        "--quota", type=float, default=50,
        help="Quota per country (default: 50)"
    )
    parser.add_argument(
        "--damage-parameter", type=float, default=0.01,
        help="Damage parameter (default: 0.01)"
    )
    
    args = parser.parse_args()
    
    # Create example countries
    countries = [
        Country("Country A", 40),
        Country("Country B", 60),
        Country("Country C", 30),
        Country("Country D", 55)
    ]
    
    # Simulate one period
    results = simulate_one_period(
        countries,
        args.stock,
        args.growth_rate,
        args.carrying_capacity,
        args.quota,
        args.damage_parameter
    )
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Print summary
    print("\nSummary:")
    print(f"Initial stock: {results['initial_stock']}")
    print(f"Total consumption: {results['total_consumption']}")
    print(f"Environmental damage: {results['environmental_damage']}")
    print(f"Shadow price: {results['shadow_price']}")
    print(f"Next period stock: {results['next_stock']}")
    print(f"All proofs verified: {results['proofs_verified']}")


if __name__ == "__main__":
    main()