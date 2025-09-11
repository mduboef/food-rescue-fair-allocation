import os
import sys
import csv
import random
import numpy as np
from colorama import Fore

from donor import Donor, readDonorData
from agency import Agency, Preference, readAgencyData
from driver import Driver
from algos import plotBipartiteGraph

def main():

    # read in agency data
    agencies = readAgencyData("resources/CURRENT_AgencyList8-2025.xlsx", "resources/FoodEquityPoundsFoodTypeSummary2023Statistics.xlsx")
    # read in donor data
    donors = readDonorData("resources/donorData.csv")

    # populate adjancency matrix connecting agencies to donors if feasible
    # TODO start by populating them at random

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
            if random.random() < 0.15:  # 30% chance of a connection
                adjMatrix[i][j] = 1
    

    plotBipartiteGraph(adjMatrix, donorLabels, agencyLabels)


    return 0

main()