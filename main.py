import os
import sys
import csv
import random
import numpy as np
from colorama import Fore

from item import Item
from donor import readDonorData
from agency import Agency, Preference, readAgencyData
from driver import Driver, generateDrivers
from visuals import plotBipartiteGraph, plotAllocationGraph, plotComparisonGraphs
from algos import egalitarianILP, printAllocationSummary, randItemGen

seed = 3

random.seed(seed)


def main():

    # read in agency data
    agencies = readAgencyData("resources/agencyData_small.csv")
    # read in donor data
    donors = readDonorData("resources/donorData_small.csv")
    # generate time steps
    timesteps = range(10)

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
            elif random.random() < 1.00:  # 7% chance of a connection
                adjMatrix[i][j] = 1

    print(f"\nAdjacency Matrix Shape: {adjMatrix.shape}")
    print(f"Possible connections: {int(np.sum(adjMatrix))}")

    # # visualize the network
    # plotBipartiteGraph(adjMatrix, donorLabels, agencyLabels)

    # randomly assign packages to donors with new food type support
    items = randItemGen(
        donors,
        timesteps,
        minItems=3,
        maxItems=25,
        minWeight=10,
        maxWeight=50,
        seed=seed,
    )

    # run new ILP egalitarian with drivers and food types
    allocation, agencyUtilities = egalitarianILP(
        donors, agencies, items, timesteps, adjMatrix, drivers, use_gurobi=False
    )
    # printAllocationSummary(allocation, items, agencies, donors, agencyUtilities)

    # visualize
    print("\nDisplaying network comparison...")
    plotComparisonGraphs(
        adjMatrix, allocation, donors, agencies, donorLabels, agencyLabels
    )

    return 0


if __name__ == "__main__":
    main()
