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
    agencies = readAgencyData("CURRENT_AgencyList8-2025.xlsx", "FoodEquityPoundsFoodTypeSummary2023Statistics.xlsx")

    # read in donor data
    donors = readDonorData("donorData.csv")

    # populate adjancency matrix connecting agencies to donors if feasible
    # TODO start by populating them at random

    adjMatrix = np.zeros((10, 10))  # placeholder for actual size

    # set array of donor names
    donorLabels = []
    for i in range(len(donors)):
        donorLabels.append(donors[i].name)
    
    # set array of agency names
    agencyLabels = []
    for i in range(len(agencies)):
        agencyLabels.append(agencies[i].name)


    return 0