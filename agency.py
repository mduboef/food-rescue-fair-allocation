import csv


class Preference:
	def __init__(self, level):
		self.level = level


class Agency:
	def __init__(self, name):
		self.name = name
		self.fbwmPartner = None   # NFB, FBNE or FBE
		self.deliveredPerWk = 0  # meals delivered per week by RT in 2023
		self.servedPerWk = 0     # meals served per week in 2023
		self.entitlement = 0     # will be calculated as servedPerWk - deliveredPerWk
		self.fridgeCount = None
		self.freezerCount = None
		self.foodTypeData = {}  # dictionary to store food type percentages

		self.city = None
		self.state = None
		self.address = None
		self.zip = None
		self.latitude = None
		self.longitude = None


# reads agency data from CSV file
def readAgencyData(agencyDataPath):
	agencies = []
	
	try:
		with open(agencyDataPath, 'r', encoding='utf-8') as file:
			reader = csv.DictReader(file)
			
			for row in reader:
				# skip empty rows
				if not row.get('Name') or not row['Name'].strip():
					continue
				
				# create agency object
				agency = Agency(row['Name'].strip())
				
				# populate location data
				if row.get('Address'):
					agency.address = row['Address'].strip()
				
				if row.get('City'):
					agency.city = row['City'].strip()
				
				if row.get('State'):
					agency.state = row['State'].strip()
				
				if row.get('Zip'):
					agency.zip = row['Zip'].strip()
				
				# populate coordinates
				if row.get('Latitude'):
					try:
						agency.latitude = float(row['Latitude'])
					except (ValueError, TypeError):
						agency.latitude = None
				
				if row.get('Longitude'):
					try:
						agency.longitude = float(row['Longitude'])
					except (ValueError, TypeError):
						agency.longitude = None
				
				# populate FBWM partnership status
				if row.get('FBWM'):
					fbwmStr = row['FBWM'].strip().upper()
					if fbwmStr == 'NFB':
						agency.fbwmPartner = False
					elif fbwmStr in ['FBE', 'FBNE']:
						agency.fbwmPartner = fbwmStr
					else:
						agency.fbwmPartner = None
				
				# populate storage capacity
				if row.get('Fridge'):
					try:
						agency.fridgeCount = int(row['Fridge'])
					except (ValueError, TypeError):
						agency.fridgeCount = None
				
				if row.get('Freezer'):
					try:
						agency.freezerCount = int(row['Freezer'])
					except (ValueError, TypeError):
						agency.freezerCount = None
				
				# populate meals data
				if row.get('MS'):
					try:
						agency.servedPerWk = float(row['MS'])
					except (ValueError, TypeError):
						agency.servedPerWk = 0
				
				if row.get('MD'):
					try:
						agency.deliveredPerWk = float(row['MD'])
					except (ValueError, TypeError):
						agency.deliveredPerWk = 0
				
				# calculate entitlement
				agency.entitlement = agency.servedPerWk - agency.deliveredPerWk
				
				agencies.append(agency)
		
		print(f"Successfully loaded {len(agencies)} agencies from {agencyDataPath}")
		return agencies
		
	except FileNotFoundError:
		print(f"Error: File not found: {agencyDataPath}")
		return []
	except Exception as e:
		print(f"Error reading agency data: {str(e)}")
		return []