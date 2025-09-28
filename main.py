import os
import sys
import csv
import random
import numpy as np
from colorama import Fore

from donor import Item, Donor, readDonorData
from agency import Agency, Preference, readAgencyData
from driver import Driver
from visuals import plotBipartiteGraph, plotAllocationGraph, plotComparisonGraphs
from algos import leximinGreedy, printAllocationSummary, randItemGen

def main():

    # read in agency data
    agencies = readAgencyData("resources/CURRENT_AgencyList8-2025.xlsx", "resources/FoodEquityPoundsFoodTypeSummary2023Statistics.xlsx")
    # read in donor data
    donors = readDonorData("resources/donorData.csv")

    # populate adjancency matrix connecting agencies to donors if feasible

    adjMatrix = np.zeros((len(donors), len(agencies)))  # ? Is this right way round? donors should be rows, agencies columns

    # set array of donor names
    donorLabels = []
    for i in range(len(donors)):
        donorLabels.append(donors[i].name)
    
    # set array of agency names
    agencyLabels = []
    for i in range(len(agencies)):
        agencyLabels.append(agencies[i].name)

    # randomly populate the adjacency matrix TEMPORARY
    for i in range(len(donors)):
        for j in range(len(agencies)):

            # if donor is FBWM partner and agency is not, no connection
            if donors[i].fbwmPartner == True and agencies[j].fbwmPartner == False:
                continue
            
            # TODO add city/neighborhood data so that this os more sparse
            # elif donors[i].city != agencies[j].city:
            #     adjMatrix[i][j] = 1

            elif random.random() < 0.07:  # 15% chance of a connection
                adjMatrix[i][j] = 1
    
    print(adjMatrix)

    # plotBipartiteGraph2(adjMatrix, donorLabels, agencyLabels)
    plotBipartiteGraph(adjMatrix, donorLabels, agencyLabels)


    # radomly assign packages to donors
    randItemGen(donors, minItems=3, maxItems=20, minWeight=10, maxWeight=50)

    # perform leximin greedy algorithm to assign donor's items to agencies
    allocation, agencyUtilities = leximinGreedy(donors, agencies, adjMatrix)

    printAllocationSummary(allocation, agencies, donors, agencyUtilities)

    # # visualize allocation results
    # print("\nDisplaying allocation results...")
    # plotAllocationGraph(allocation, donors, agencies, donorLabels, agencyLabels)
    
    # show side-by-side comparison
    print("\nDisplaying network comparison...")
    plotComparisonGraphs(adjMatrix, allocation, donors, agencies, donorLabels, agencyLabels)

    return 0

main()