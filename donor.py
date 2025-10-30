import csv


class Item:
    def __init__(self, foodType, weight):
        self.foodType = foodType  # list of applicable food categories (legacy)
        self.weight = weight  # in pounds
        self.availabilityTime = None
        self.probability = 1.0  # probability of availability

        # new food type quantities for the updated formulation
        # foodTypeQuantities[foodType] = pounds of that food type in this item
        self.foodTypeQuantities = {}  # dict mapping food type to quantity in pounds


class Donor:
    def __init__(self, name, fbwmPartner):
        self.name = name
        self.fbwmPartner = fbwmPartner  # True if FBWM donor, False otherwise
        self.items = []  # list of item objects

        self.city = None
        self.state = None
        self.address = None
        self.zip = None
        self.latitude = None
        self.longitude = None

        # food type percentages
        self.breadPercent = None
        self.dairyPercent = None
        self.preparedPercent = None
        self.nonPerishablePercent = None
        self.producePercent = None
        self.proteinPercent = None
        self.hygienePercent = None


# reads donor data from CSV file
def readDonorData(filename):
    donors = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                # skip empty rows
                if not row.get("Name") or not row["Name"].strip():
                    continue

                name = row["Name"].strip()

                # check if donor has '*' in name (legacy format) or FBWM column
                if "*" in name:
                    fbwmPartner = True
                    name = name.replace("*", "").strip()
                elif row.get("FBWM"):
                    fbwmStr = row["FBWM"].strip().upper()
                    fbwmPartner = fbwmStr in ["Y", "YES", "TRUE", "1"]
                else:
                    fbwmPartner = False

                # create donor object
                donor = Donor(name, fbwmPartner)

                # populate location data
                if row.get("Address"):
                    donor.address = row["Address"].strip()

                if row.get("City"):
                    donor.city = row["City"].strip()

                if row.get("State"):
                    donor.state = row["State"].strip()

                if row.get("Zip"):
                    donor.zip = row["Zip"].strip()

                # populate coordinates
                if row.get("Latitude"):
                    try:
                        donor.latitude = float(row["Latitude"])
                    except (ValueError, TypeError):
                        donor.latitude = None

                if row.get("Longitude"):
                    try:
                        donor.longitude = float(row["Longitude"])
                    except (ValueError, TypeError):
                        donor.longitude = None

                # populate food type percentages
                if row.get("Bread%"):
                    try:
                        donor.breadPercent = float(row["Bread%"])
                    except (ValueError, TypeError):
                        donor.breadPercent = None

                if row.get("Dairy%"):
                    try:
                        donor.dairyPercent = float(row["Dairy%"])
                    except (ValueError, TypeError):
                        donor.dairyPercent = None

                if row.get("Prepared%"):
                    try:
                        donor.preparedPercent = float(row["Prepared%"])
                    except (ValueError, TypeError):
                        donor.preparedPercent = None

                if row.get("Non-Perishable%"):
                    try:
                        donor.nonPerishablePercent = float(row["Non-Perishable%"])
                    except (ValueError, TypeError):
                        donor.nonPerishablePercent = None

                if row.get("Produce%"):
                    try:
                        donor.producePercent = float(row["Produce%"])
                    except (ValueError, TypeError):
                        donor.producePercent = None

                if row.get("Protein%"):
                    try:
                        donor.proteinPercent = float(row["Protein%"])
                    except (ValueError, TypeError):
                        donor.proteinPercent = None

                if row.get("Hygiene%"):
                    try:
                        donor.hygienePercent = float(row["Hygiene%"])
                    except (ValueError, TypeError):
                        donor.hygienePercent = None

                donors.append(donor)

        print(f"Successfully loaded {len(donors)} donors from {filename}")
        return donors

    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        return []
    except Exception as e:
        print(f"Error reading donor data: {str(e)}")
        return []
