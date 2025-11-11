class Item:
    def __init__(self, donor, timestep, weight, foodType):
        self.donor = donor  # object from the class donor, corresponding to the donor that donated the item
        self.timestep = timestep
        self.weight = weight  # in pounds
        self.foodType = foodType  # list of applicable food categories (legacy)
        self.availabilityTime = None
        self.probability = 1.0  # probability of availability

        # new food type quantities for the updated formulation
        # foodTypeQuantities[foodType] = pounds of that food type in this item
        self.foodTypeQuantities = {}  # dict mapping food type to quantity in pounds
