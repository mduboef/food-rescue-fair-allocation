import datetime
import pandas as pd


class Preference:
    def __init__(self, level):
        self.level = level

class Agency:
    def __init__(self, name):
        self.name = name
        self.openingTime = None
        self.closingTime = None
        self.type = None        # e.g., shelter, food bank, etc.
        self.fbwmType = None
        self.deliveredPerWk = 0  # meals delivered per year
        self.servedPerWk = 0     # meals served per year

    # from CURRENT_AgencyList8-2025.xlsx
        # Name
        # City
        # Contact
        # Hours
        # Food Bank Bool
        # Do they have a truck/van Bool
        # Equipment
        # List of needs
        # Num of people served per week

    # from FoodEquityPoundsFoodTypeSummary2023Statistics.xlsx
        # FBWM Designation
        # Meals delivered per week
        # Meals served per week
            # sanity check with CurrentAgencyList 
        # Type of agency (Food Pantry, MS or RF)
        # Food Type Data
def readAgencyData(filename1, filename2):


