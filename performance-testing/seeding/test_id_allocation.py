#!/usr/bin/env python3
"""Test script to verify pod-specific ID allocation prevents duplicates.

This script simulates multiple pods generating IDs and checks for collisions.
"""

import sys
sys.path.insert(0, ".")

from id_scheme import init_pod_id_scheme, assign_functional_id


def test_id_allocation(tier: str, total_pods: int):
    """Test ID allocation across multiple pods."""
    
    # Load config to get farmer count
    import config
    total_farmers = config.DATA_VOLUME_TIERS[tier]
    
    print(f"Testing ID allocation for tier '{tier}' ({total_farmers} farmers, {total_pods} pods)")
    
    # Initialize ID schemes for each pod
    pod_schemes = []
    for pod_index in range(total_pods):
        init_pod_id_scheme(pod_index, total_pods, total_farmers)
        pod_schemes.append(pod_index)
    
    # Generate some IDs from each pod and check for collisions
    farmer_ids = set()
    household_ids = set()
    
    test_iterations = 1000
    
    for pod_index in range(total_pods):
        # Reinitialize for this pod
        init_pod_id_scheme(pod_index, total_pods, total_farmers)
        
        print(f"  Pod {pod_index}:")
        
        # Generate test IDs
        pod_farmer_ids = []
        pod_household_ids = []
        
        for _ in range(test_iterations):
            farmer_id = assign_functional_id("Farmer")
            household_id = assign_functional_id("Household")
            
            pod_farmer_ids.append(farmer_id)
            pod_household_ids.append(household_id)
        
        # Check for collisions within this pod
        if len(pod_farmer_ids) != len(set(pod_farmer_ids)):
            print(f"    ERROR: Duplicate farmer IDs within pod {pod_index}")
            return False
        
        if len(pod_household_ids) != len(set(pod_household_ids)):
            print(f"    ERROR: Duplicate household IDs within pod {pod_index}")
            return False
        
        # Check for collisions with other pods
        for farmer_id in pod_farmer_ids:
            if farmer_id in farmer_ids:
                print(f"    ERROR: Duplicate farmer ID {farmer_id} across pods")
                return False
            farmer_ids.add(farmer_id)
        
        for household_id in pod_household_ids:
            if household_id in household_ids:
                print(f"    ERROR: Duplicate household ID {household_id} across pods")
                return False
            household_ids.add(household_id)
        
        print(f"    Generated {test_iterations} unique farmer IDs")
        print(f"    Generated {test_iterations} unique household IDs")
        print(f"    Farmer ID range: {pod_farmer_ids[0]} to {pod_farmer_ids[-1]}")
        print(f"    Household ID range: {pod_household_ids[0]} to {pod_household_ids[-1]}")
    
    print(f"\n✓ SUCCESS: No ID collisions detected across {total_pods} pods")
    print(f"  Total unique farmer IDs: {len(farmer_ids)}")
    print(f"  Total unique household IDs: {len(household_ids)}")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test pod-specific ID allocation")
    parser.add_argument("--tier", default="primary", help="Data volume tier")
    parser.add_argument("--pods", type=int, default=10, help="Number of pods to simulate")
    
    args = parser.parse_args()
    
    success = test_id_allocation(args.tier, args.pods)
    sys.exit(0 if success else 1)