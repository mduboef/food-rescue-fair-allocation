import datetime
import pandas as pd
import openpyxl
import re


class Preference:
    def __init__(self, level):
        self.level = level

class Agency:
    def __init__(self, name):
        self.name = name
        self.city = None
        self.contact = None
        self.openingTime = None
        self.closingTime = None
        self.type = None        # e.g., FP (Food Pantry), MS (Meal Service), RF (Residential Facility)
        self.fbwmType = None    # Food Bank relationship: Y/N from equity data
        self.deliveredPerWk = 0  # meals delivered per week
        self.servedPerWk = 0     # meals served per week
        self.equipment = None
        self.hasTruckVan = None
        self.needs = None
        self.peopleServedWeekly = None
        self.mealDistributionTimes = None
        self.isFoodBankAgency = None
        self.poundsDelivered2023 = None
        self.clientsPerWeek = None
        self.foodTypeData = {}  # dictionary to store food type percentages

# helper function to extract agency name from full name/address string
def extractAgencyName(fullNameAddress):
    if not fullNameAddress:
        return ""
    
    # split by newline and take the first part (agency name)
    lines = fullNameAddress.split('\n')
    agencyName = lines[0].strip()
    
    # remove any trailing punctuation or extra whitespace
    agencyName = re.sub(r'[,\s]*$', '', agencyName)
    
    return agencyName

# helper function to normalize agency names for matching
def normalizeAgencyName(name):
    if not name:
        return ""
    
    # convert to lowercase, remove extra spaces, and common variations
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # multiple spaces to single space
    normalized = re.sub(r'[,\.]*$', '', normalized)  # remove trailing punctuation
    
    # handle common abbreviations and variations
    replacements = {
        'the ': '',
        ' inc': '',
        ' inc.': '',
        ' llc': '',
        ' ltd': '',
        'center': 'ctr',
        'centre': 'ctr',
        'community': 'comm',
        'salvation army': 'sal army',
        'church': 'ch',
        'pantry': 'pantry',
        'food bank': 'fb'
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized.strip()

# helper function to find best match between agency names
def findBestMatch(targetName, agencyList, threshold=0.7):
    """
    finds the best matching agency name from a list
    returns (matched_agency, confidence_score) or (None, 0) if no good match
    """
    import difflib
    
    normalizedTarget = normalizeAgencyName(targetName)
    
    bestMatch = None
    bestScore = 0
    
    for agency in agencyList:
        normalizedCandidate = normalizeAgencyName(agency)
        
        # use difflib for fuzzy matching
        score = difflib.SequenceMatcher(None, normalizedTarget, normalizedCandidate).ratio()
        
        if score > bestScore and score >= threshold:
            bestScore = score
            bestMatch = agency
    
    return bestMatch, bestScore

# helper function to parse hours string and extract opening/closing times
def parseHours(hoursString):
    """
    attempts to parse opening/closing times from hours string
    returns tuple (openingTime, closingTime) or (None, None) if can't parse
    """
    if not hoursString or pd.isna(hoursString):
        return None, None
    
    # this is a simple implementation - could be expanded for more complex parsing
    # look for patterns like "9 am - 5 pm" or "9:00 - 17:00"
    hourPattern = r'(\d{1,2}(?::\d{2})?)\s*([ap]m?)?\s*[-–]\s*(\d{1,2}(?::\d{2})?)\s*([ap]m?)?'
    match = re.search(hourPattern, hoursString.lower())
    
    if match:
        # for now, just return the string representation
        # could be converted to datetime objects if needed
        return match.group(0), match.group(0)
    
    return None, None

def readAgencyData(agencyListPath, equitySummaryPath):
    """
    reads agency data from both Excel files and returns list of populated Agency objects
    """
    agencies = []
    
    try:
        # read current agency list
        print("Reading current agency list...")
        currentAgencyDf = pd.read_excel(agencyListPath, sheet_name=0)
        
        # read food equity summary data
        print("Reading food equity summary...")
        equityDf = pd.read_excel(equitySummaryPath, sheet_name="Pounds Data Analysis")
        
        # read food type data 
        foodTypeDf = pd.read_excel(equitySummaryPath, sheet_name="Food Type Data Analysis")
        
        # create agencies from current agency list
        agencyNameToObj = {}
        currentAgencyNames = []
        
        for index, row in currentAgencyDf.iterrows():
            if pd.isna(row.iloc[0]) or not row.iloc[0]:
                continue
                
            # extract agency name from full name/address
            fullNameAddress = str(row.iloc[0])
            agencyName = extractAgencyName(fullNameAddress)
            
            if not agencyName:
                continue
                
            currentAgencyNames.append(agencyName)
            
            # create agency object
            agency = Agency(agencyName)
            
            # populate data from current agency list
            if len(row) > 1 and not pd.isna(row.iloc[1]):
                agency.city = str(row.iloc[1]).strip()
            
            if len(row) > 2 and not pd.isna(row.iloc[2]):
                agency.contact = str(row.iloc[2]).strip()
            
            if len(row) > 3 and not pd.isna(row.iloc[3]):
                hoursString = str(row.iloc[3]).strip()
                agency.openingTime, agency.closingTime = parseHours(hoursString)
            
            if len(row) > 4 and not pd.isna(row.iloc[4]):
                agency.equipment = str(row.iloc[4]).strip()
            
            if len(row) > 5 and not pd.isna(row.iloc[5]):
                truckVanString = str(row.iloc[5]).strip().upper()
                agency.hasTruckVan = "YES" in truckVanString
            
            if len(row) > 6 and not pd.isna(row.iloc[6]):
                agency.needs = str(row.iloc[6]).strip()
            
            if len(row) > 7 and not pd.isna(row.iloc[7]):
                agency.peopleServedWeekly = str(row.iloc[7]).strip()
            
            if len(row) > 8 and not pd.isna(row.iloc[8]):
                agency.mealDistributionTimes = str(row.iloc[8]).strip()
            
            if len(row) > 9 and not pd.isna(row.iloc[9]):
                fbString = str(row.iloc[9]).strip().upper()
                agency.isFoodBankAgency = "YES" in fbString or "Y" == fbString
            
            agencyNameToObj[agencyName] = agency
        
        # now process equity summary data
        equityAgencyNames = []
        
        for index, row in equityDf.iterrows():
            if pd.isna(row.iloc[0]) or not row.iloc[0]:
                continue
                
            agencyName = str(row.iloc[0]).strip()
            
            # skip header rows and section dividers
            if (agencyName.startswith('*') or 
                'Non-Food Bank' in agencyName or 
                'Food Bank Enabled' in agencyName or 
                'Delivered to' in agencyName):
                continue
            
            equityAgencyNames.append(agencyName)
            
            # try to find matching agency in current list
            matchedName, confidence = findBestMatch(agencyName, currentAgencyNames)
            
            if matchedName and confidence > 0.7:
                # found a good match, update the agency object
                agency = agencyNameToObj[matchedName]
                
                # populate equity data
                if len(row) > 1 and not pd.isna(row.iloc[1]):
                    agency.poundsDelivered2023 = float(row.iloc[1])
                
                if len(row) > 2 and not pd.isna(row.iloc[2]):
                    agency.type = str(row.iloc[2]).strip()
                
                if len(row) > 3 and not pd.isna(row.iloc[3]):
                    agency.clientsPerWeek = float(row.iloc[3])
                
                if len(row) > 5 and not pd.isna(row.iloc[5]):
                    agency.servedPerWk = float(row.iloc[5])
                
                if len(row) > 6 and not pd.isna(row.iloc[6]):
                    agency.deliveredPerWk = float(row.iloc[6])
                
                if len(row) > 12 and not pd.isna(row.iloc[12]):
                    fbwmString = str(row.iloc[12]).strip().upper()
                    agency.fbwmType = fbwmString
            else:
                # agency in equity summary but not in current list - disregard per instructions
                print(f"Warning: Agency '{agencyName}' found in equity summary but not in current agency list (disregarding)")
        
        # process food type data
        for index, row in foodTypeDf.iterrows():
            if pd.isna(row.iloc[1]) or not row.iloc[1]:
                continue
                
            agencyName = str(row.iloc[1]).strip()
            
            # skip section headers
            if ('Non-Food Bank' in agencyName or 
                'Food Bank Enabled' in agencyName):
                continue
            
            # try to find matching agency
            matchedName, confidence = findBestMatch(agencyName, currentAgencyNames)
            
            if matchedName and confidence > 0.7:
                agency = agencyNameToObj[matchedName]
                
                # populate food type data (columns 2-15 contain food type percentages and z-scores)
                foodTypes = ['Bread & Bakery', 'Dairy & Eggs', 'Prepared Foods', 
                           'Non-perishables', 'Produce', 'Meat & Protein', 'Cleaning & Hygiene']
                
                for i, foodType in enumerate(foodTypes):
                    colIndex = 2 + (i * 2)  # food type percentages are in every other column starting at 2
                    if len(row) > colIndex and not pd.isna(row.iloc[colIndex]):
                        agency.foodTypeData[foodType] = float(row.iloc[colIndex])
        
        # create final list of agencies and check for missing agencies
        agencies = list(agencyNameToObj.values())
        
        # check for agencies in current list that don't appear in equity summary
        equityAgencyNamesNormalized = [normalizeAgencyName(name) for name in equityAgencyNames]
        
        for agencyName in currentAgencyNames:
            normalizedCurrent = normalizeAgencyName(agencyName)
            found = False
            
            for normalizedEquity in equityAgencyNamesNormalized:
                if (normalizedCurrent == normalizedEquity or 
                    normalizedCurrent in normalizedEquity or 
                    normalizedEquity in normalizedCurrent):
                    found = True
                    break
            
            if not found:
                print(f"Warning: Agency '{agencyName}' appears in current agency list but not in 2023 equity summary")
        
        print(f"Successfully loaded {len(agencies)} agencies")
        return agencies
        
    except Exception as e:
        print(f"Error reading agency data: {str(e)}")
        return []

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