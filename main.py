import os
import sys
import csv
import random
import numpy as np
from colorama import Fore

from donor import Item, Donor, readDonorData
from agency import Agency, Preference, readAgencyData
from driver import Driver, generateDrivers
from visuals import plotBipartiteGraph, plotAllocationGraph, plotComparisonGraphs
from algos import leximinGreedy, egalitarianILP, printAllocationSummary, randItemGen

def main():

	# read in agency data
	agencies = readAgencyData("resources/agencyData.csv")
	# read in donor data
	donors = readDonorData("resources/donorData.csv")
	
	# generate drivers for the new formulation
	drivers = generateDrivers(5)  # create 5 drivers with random locations

	# populate adjacency matrix connecting agencies to donors if feasible
	adjMatrix = np.zeros((len(donors), len(agencies)))

	# set array of donor names
	donorLabels = []
	for i in range(len(donors)):
		donorLabels.append(donors[i].name)
	
	# set array of agency names
	agencyLabels = []
	for i in range(len(agencies)):
		agencyLabels.append(agencies[i].name)

	# populate adjacency matrix with edges
	for i in range(len(donors)):
		for j in range(len(agencies)):

			# if donor is FBWM partner and agency is not, no connection
			if donors[i].fbwmPartner == True and agencies[j].fbwmPartner == "NFB":
				continue

			# TODO populate the adjacency matrix based the lat/long of donors and agencies
			# ! Still need lat/long data for donors

			# TEMPORARY randomly generate edges
			elif random.random() < 0.07:  # 7% chance of a connection
				adjMatrix[i][j] = 1

	
	print(f"\nAdjacency Matrix Shape: {adjMatrix.shape}")
	print(f"Possible connections: {int(np.sum(adjMatrix))}")

	# # visualize the network
	# plotBipartiteGraph(adjMatrix, donorLabels, agencyLabels)

	# randomly assign packages to donors with new food type support
	randItemGen(donors, minItems=3, maxItems=25, minWeight=10, maxWeight=50)

	# choose which algorithm to run
	print("\n" + "="*60)
	print("ALLOCATION ALGORITHM OPTIONS")
	print("="*60)
	print("1. Leximin Greedy (Legacy)")
	print("2. ILP Egalitarian (New Formulation)")
	print("3. Compare Both")
	print("="*60)
	
	choice = input("\nSelect option (1, 2, or 3): ").strip()

	if choice == "1":
		# run greedy leximin
		print("\n" + "="*60)
		print("RUNNING GREEDY LEXIMIN ALGORITHM")
		print("="*60)
		allocation, agencyUtilities = leximinGreedy(donors, agencies, adjMatrix)
		printAllocationSummary(allocation, agencies, donors, agencyUtilities)
		
		# visualize
		print("\nDisplaying network comparison...")
		plotComparisonGraphs(adjMatrix, allocation, donors, agencies, donorLabels, agencyLabels)

	elif choice == "2":
		# run new ILP egalitarian with drivers and food types
		allocation, agencyUtilities = egalitarianILP(donors, agencies, adjMatrix, drivers)
		printAllocationSummary(allocation, agencies, donors, agencyUtilities)
		
		# visualize
		print("\nDisplaying network comparison...")
		plotComparisonGraphs(adjMatrix, allocation, donors, agencies, donorLabels, agencyLabels)

	elif choice == "3":
		# compare both approaches
		print("\n" + "="*60)
		print("RUNNING GREEDY LEXIMIN ALGORITHM")
		print("="*60)
		greedyAllocation, greedyUtilities = leximinGreedy(donors, agencies, adjMatrix)
		
		print("\n" + "="*60)
		print("RUNNING NEW ILP EGALITARIAN ALGORITHM")
		print("="*60)
		ilpAllocation, ilpUtilities = egalitarianILP(donors, agencies, adjMatrix, drivers)
		
		# compare results
		print("\n" + "="*80)
		print("COMPARISON: GREEDY vs NEW ILP")
		print("="*80)
		
		# calculate min MDMS for each approach
		greedyMDMSValues = []
		ilpMDMSValues = []
		
		for agencyIdx, agency in enumerate(agencies):
			if agency.servedPerWk and agency.servedPerWk > 0:
				greedyMDMS = greedyUtilities[agencyIdx] / agency.servedPerWk
				ilpMDMS = ilpUtilities[agencyIdx] / agency.servedPerWk
				greedyMDMSValues.append(greedyMDMS)
				ilpMDMSValues.append(ilpMDMS)
		
		if greedyMDMSValues:
			greedyMin = min(greedyMDMSValues)
			ilpMin = min(ilpMDMSValues)
			greedyAvg = sum(greedyMDMSValues) / len(greedyMDMSValues)
			ilpAvg = sum(ilpMDMSValues) / len(ilpMDMSValues)
			greedyMax = max(greedyMDMSValues)
			ilpMax = max(ilpMDMSValues)
			
			print(f"\n{'Metric':<30} {'Greedy':<15} {'New ILP':<15} {'Improvement':<15}")
			print("-" * 80)
			print(f"{'Min MDMS':<30} {greedyMin:<15.3f} {ilpMin:<15.3f} {(ilpMin/greedyMin - 1)*100:>13.1f}%")
			print(f"{'Avg MDMS':<30} {greedyAvg:<15.3f} {ilpAvg:<15.3f} {(ilpAvg/greedyAvg - 1)*100:>13.1f}%")
			print(f"{'Max MDMS':<30} {greedyMax:<15.3f} {ilpMax:<15.3f} {(ilpMax/greedyMax - 1)*100:>13.1f}%")
			print(f"{'MDMS Range':<30} {greedyMax-greedyMin:<15.3f} {ilpMax-ilpMin:<15.3f} {((ilpMax-ilpMin)/(greedyMax-greedyMin) - 1)*100:>13.1f}%")
			
			greedyTotal = sum(greedyUtilities)
			ilpTotal = sum(ilpUtilities)
			print(f"{'Total food allocated (lbs)':<30} {greedyTotal:<15.1f} {ilpTotal:<15.1f} {(ilpTotal/greedyTotal - 1)*100:>13.1f}%")
			
			# count how many agencies received food
			greedyServed = sum(1 for u in greedyUtilities if u > 0)
			ilpServed = sum(1 for u in ilpUtilities if u > 0)
			print(f"{'Agencies served':<30} {greedyServed:<15} {ilpServed:<15} {ilpServed - greedyServed:>14}")
		
		# visualize both
		print("\nDisplaying New ILP allocation results...")
		plotComparisonGraphs(adjMatrix, ilpAllocation, donors, agencies, donorLabels, agencyLabels)

	else:
		print("Invalid choice. Exiting.")
		return 1

	return 0

if __name__ == "__main__":
	main()
