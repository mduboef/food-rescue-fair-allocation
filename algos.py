import numpy as np
import random
from collections import defaultdict
from pulp import *

from donor import Item, Donor


# ILP-based allocation with egalitarian (max-min) welfare
def egalitarianILP(donors, agencies, adjMatrix):
	
	print(f"\n{'='*60}")
	print("STARTING ILP SOLVER - EGALITARIAN WELFARE")
	print(f"{'='*60}")
	
	# create the optimization model
	model = LpProblem("Food_Allocation_Egalitarian", LpMaximize)
	
	# decision variables: x[d,a,i] = 1 if item i from donor d goes to agency a
	x = {}
	for donorIdx, donor in enumerate(donors):
		for itemIdx, item in enumerate(donor.items):
			for agencyIdx, agency in enumerate(agencies):
				varName = f"x_d{donorIdx}_a{agencyIdx}_i{itemIdx}"
				x[(donorIdx, agencyIdx, itemIdx)] = LpVariable(varName, cat='Binary')
	
	print(f"Created {len(x)} decision variables")
	
	# calcuate total food received by each agency in lbs
	foodReceived = {}
	for agencyIdx in range(len(agencies)):
		foodReceived[agencyIdx] = LpVariable(f"food_a{agencyIdx}", lowBound=0)
	
	# calculate MDMS (Meals Delivered / Meals Served) for each agency
	mdms = {}
	for agencyIdx in range(len(agencies)):
		mdms[agencyIdx] = LpVariable(f"mdms_a{agencyIdx}", lowBound=0)
	
	# minimum MDMS across all agencies
	minMDMS = LpVariable("min_mdms", lowBound=0)        # our objective is to maximize this
	
	# objective: maximize the minimum MDMS
	model += minMDMS, "Maximize_Minimum_MDMS"
	
	# constraint 1: each item delivered at most once
	for donorIdx, donor in enumerate(donors):
		for itemIdx, item in enumerate(donor.items):
			model += (
				lpSum(x[(donorIdx, agencyIdx, itemIdx)] 
					  for agencyIdx in range(len(agencies))) <= 1,
				f"Item_d{donorIdx}_i{itemIdx}_once"
			)
	
	# constraint 2: follow the adjacency matrix and only use feasible routes
	constraintsAdded = 0
	for donorIdx in range(len(donors)):
		for itemIdx in range(len(donors[donorIdx].items)):
			for agencyIdx in range(len(agencies)):
				if adjMatrix[donorIdx][agencyIdx] == 0:
					model += (
						x[(donorIdx, agencyIdx, itemIdx)] == 0,
						f"Infeasible_d{donorIdx}_a{agencyIdx}_i{itemIdx}"
					)
					constraintsAdded += 1
	
	print(f"Added {constraintsAdded} adjacency constraints")
	
	
	# calculate total food received by each agency
	for agencyIdx in range(len(agencies)):
		model += (
			foodReceived[agencyIdx] == lpSum(
				x[(donorIdx, agencyIdx, itemIdx)] * donors[donorIdx].items[itemIdx].weight
				for donorIdx in range(len(donors))
				for itemIdx in range(len(donors[donorIdx].items))
			),
			f"FoodReceived_a{agencyIdx}"
		)
	
	# calculate MDMS for each agency
	validAgencies = 0
	for agencyIdx, agency in enumerate(agencies):
		if agency.servedPerWk and agency.servedPerWk > 0:
			model += (
				mdms[agencyIdx] == foodReceived[agencyIdx] / agency.servedPerWk,
				f"MDMS_a{agencyIdx}"
			)
			validAgencies += 1
		else:
			# if no service data, set MDMS to 0
			model += (
				mdms[agencyIdx] == 0,
				f"MDMS_a{agencyIdx}_nodata"
			)
	
	print(f"Optimizing for {validAgencies} agencies with valid service data")
	
	# constraint 3: minMDMS must be <= all agency MDMS values
	for agencyIdx in range(len(agencies)):
		if agencies[agencyIdx].servedPerWk and agencies[agencyIdx].servedPerWk > 0:
			model += (
				minMDMS <= mdms[agencyIdx],
				f"MinMDMS_bound_a{agencyIdx}"
			)
	
	# solve the ILP
	print(f"\nSolving ILP optimization problem...")
	
	solver = PULP_CBC_CMD(msg=1, timeLimit=300)  # 5 minute time limit
	model.solve(solver)
	
	print(f"\n{'='*60}")
	print(f"ILP Solution Status: {LpStatus[model.status]}")
	
	if model.status == LpStatusOptimal:
		print(f"Optimal Min MDMS: {minMDMS.varValue:.3f}")
	elif model.status == LpStatusNotSolved:
		print("WARNING: Problem not solved - check constraints")
		return defaultdict(list), [0.0] * len(agencies)
	elif model.status == LpStatusInfeasible:
		print("WARNING: Problem is infeasible - check constraints")
		return defaultdict(list), [0.0] * len(agencies)
	
	print(f"{'='*60}\n")
	
	# extract solution
	allocation = defaultdict(list)
	agencyUtilities = [0.0] * len(agencies)
	
	# print("Allocation Results:")
	for (donorIdx, agencyIdx, itemIdx), var in x.items():
		if var.varValue and var.varValue > 0.5:  # check if allocated (handle numerical errors)
			allocation[agencyIdx].append((donorIdx, itemIdx))
			item = donors[donorIdx].items[itemIdx]
			agencyUtilities[agencyIdx] += item.weight
			agency = agencies[agencyIdx]
			mdmsValue = agencyUtilities[agencyIdx] / agency.servedPerWk if agency.servedPerWk > 0 else 0
			# print(f"{donors[donorIdx].name} ----- {item.weight} lb ----> {agency.name} (MDMS: {mdmsValue:.3f})")
	
	return allocation, agencyUtilities


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
		
		# print(f"{donors[donorIdx].name} ----- {item.weight} lb ----> {agencies[targetAgencyIdx].name} (MDMS: {agencyUtilities[targetAgencyIdx]/agencies[targetAgencyIdx].servedPerWk:.3f})")
	
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