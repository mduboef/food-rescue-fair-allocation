import numpy as np
import random
from collections import defaultdict

from donor import Item, Donor


# always gives next item to the agency with lowest current utility
def leximinGreedy(donors, agencies, adjMatrix):
    
    # initialize tracking structures
    agencyUtilities = [0.0] * len(agencies)  # total pounds received by each agency
    allocation = defaultdict(list)  # allocation[agencyIdx] = list of (donorIdx, itemIdx) tuples
    
    # create list of all available items with their donor info
    availableItems = []
    for donorIdx, donor in enumerate(donors):
        for itemIdx, item in enumerate(donor.items):
            availableItems.append((donorIdx, itemIdx, item))
    
    print(f"Starting allocation of {len(availableItems)} items to {len(agencies)} agencies")
    
    # main allocation loop
    while availableItems:
        # find agency with lowest utility per person served
        minUtilityPerPerson = float('inf')
        targetAgencyIdx = -1
        
        for agencyIdx, agency in enumerate(agencies):
            if agency.servedPerWk is None or agency.servedPerWk <= 0:
                # skip agencies with no valid service data
                continue
            
            utilityPerPerson = agencyUtilities[agencyIdx] / agency.servedPerWk
            
            if utilityPerPerson < minUtilityPerPerson:
                minUtilityPerPerson = utilityPerPerson
                targetAgencyIdx = agencyIdx
        
        if targetAgencyIdx == -1:
            print("Warning: No valid agencies found with service data")
            break
        
        # find best available item for target agency
        bestItem = None
        bestItemIdx = -1
        bestUtility = 0
        
        for itemIdx, (donorIdx, itemIdxInDonor, item) in enumerate(availableItems):
            # check if this donor can deliver to target agency
            if adjMatrix[donorIdx][targetAgencyIdx] == 0:
                continue
            
            # check FBWM partnership constraints
            donor = donors[donorIdx]
            agency = agencies[targetAgencyIdx]
            
            if donor.fbwmPartner and not agency.fbwmPartner:
                # FBWM donor can't deliver to non-FBWM agency
                continue
            
            # calculate utility (item weight)
            itemUtility = item.weight
            
            if itemUtility > bestUtility:
                bestUtility = itemUtility
                bestItem = (donorIdx, itemIdxInDonor, item)
                bestItemIdx = itemIdx
        
        if bestItem is None:
            # no valid items for target agency, try next neediest agency
            print(f"No available items for agency {agencies[targetAgencyIdx].name}")
            # remove this agency temporarily or break - for now, break
            break
        
        # allocate the best item to target agency
        donorIdx, itemIdxInDonor, item = bestItem
        allocation[targetAgencyIdx].append((donorIdx, itemIdxInDonor))
        agencyUtilities[targetAgencyIdx] += item.weight
        
        # remove allocated item from available items
        availableItems.pop(bestItemIdx)
        
        print(f"{donors[donorIdx].name} ----- {item.weight} lb ----> {agencies[targetAgencyIdx].name} (MDMS: {agencyUtilities[targetAgencyIdx]/agencies[targetAgencyIdx].servedPerWk:.3f})")
    
    return allocation, agencyUtilities


# prints a summary of the allocation results
def printAllocationSummary(allocation, agencies, donors, agencyUtilities):
    print("\n" + "="*50)
    print("ALLOCATION SUMMARY")
    print("="*50)
    
    totalAllocated = 0
    allocatedAgencies = 0
    
    for agencyIdx, allocatedItems in allocation.items():
        if len(allocatedItems) > 0:
            agency = agencies[agencyIdx]
            utility = agencyUtilities[agencyIdx]
            utilityPerPerson = utility / agency.servedPerWk if agency.servedPerWk > 0 else 0
            
            print(f"{agency.name}:")
            print(f"  Total food: {utility:.1f}lbs")
            print(f"  People served/wk: {agency.servedPerWk}")
            print(f"  Per person served: {utilityPerPerson:.3f}lbs")
            print(f"  Items received: {len(allocatedItems)}")
            totalAllocated += utility
            allocatedAgencies += 1
    
    print(f"Total agencies receiving food: {allocatedAgencies}/{len(agencies)}")
    print(f"Total food allocated: {totalAllocated:.1f}lbs")
    
    # calculate fairness metrics
    utilitiesPerPerson = []
    for agencyIdx in range(len(agencies)):
        if agencies[agencyIdx].servedPerWk and agencies[agencyIdx].servedPerWk > 0:
            utilityPerPerson = agencyUtilities[agencyIdx] / agencies[agencyIdx].servedPerWk
            utilitiesPerPerson.append(utilityPerPerson)
    
    if utilitiesPerPerson:
        minUtility = min(utilitiesPerPerson)
        maxUtility = max(utilitiesPerPerson)
        avgUtility = sum(utilitiesPerPerson) / len(utilitiesPerPerson)
        
        print(f"\nFairness Metrics (lbs per person served):")
        print(f"  Minimum: {minUtility:.3f}")
        print(f"  Maximum: {maxUtility:.3f}")  
        print(f"  Average: {avgUtility:.3f}")
        print(f"  Range: {maxUtility - minUtility:.3f}")

def randItemGen(donors, minItems=1, maxItems=5, minWeight=5, maxWeight=20):
    
    for donor in donors:
        numItems = random.randint(minItems, maxItems)
        donor.items = []  # clear existing items
        
        for i in range(numItems):
            weight = random.randint(minWeight, maxWeight)
            item = Item(None, weight)  # generic food type
            donor.items.append(item)
    
    totalItems = sum(len(donor.items) for donor in donors)
    totalWeight = sum(sum(item.weight for item in donor.items) for donor in donors)
    
    print(f"Randomly generated {totalItems} items totaling {totalWeight}lbs across {len(donors)} donors")