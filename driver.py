import random


class Driver:
    def __init__(self, name):
        self.name = name
        self.vehicleType = None
        self.location = None  # (latitude, longitude)
        self.poundsHeld = 0
        self.capacity = None
        self.availableTimes = []  # list of (start, end) tuples


# generates a list of drivers with random locations
def generateDrivers(numDrivers=5, minLat=42.0, maxLat=42.5, minLon=-73.0, maxLon=-72.0):
    drivers = []

    for i in range(numDrivers):
        driver = Driver(f"Driver_{i+1}")

        # assign random location within the service area bounds
        driver.location = (
            random.uniform(minLat, maxLat),
            random.uniform(minLon, maxLon),
        )

        # set some default capacity
        driver.capacity = random.randint(50, 200)  # pounds

        drivers.append(driver)

    print(f"Generated {len(drivers)} drivers with random locations")
    return drivers
