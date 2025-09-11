import os
import sys
import csv

class Package:
    def __init__(self, foodType, weight):
        self.foodType = foodType        # list if applible food categoies
        self.weight = weight            # in pounds
        self.availbilityTime = None
        self.probability = 1.0          # probability of availability

class Donor:
    def __init__(self, name, fbwmPartner):
        self.name = name
        self.fbwmPartner = fbwmPartner      # True if FBWM donor, False otherwise
        self.packages = []                  # list of Package objects

        # ? What if the food type differ between deliveries

def readDonorData(filename):
    donors = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # ensure the row is not empty
                name = row[0].strip()
                if '*' in name:
                    fbwmPartner = True
                    name = name.replace('*', '').strip()
                else:
                    fbwmPartner = False
                    name = name.replace('*', '').strip()
                donor = Donor(name, fbwmPartner)
                donors.append(donor)