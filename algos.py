import numpy as np
import random
from collections import defaultdict
import pulp as plp
import statistics

from donor import Item, Donor

# define the seven food types as specified
FOOD_TYPES = [
    "dairy",
    "meat",
    "produce",
    "grain",
    "processed",
    "non-perishables",
    "hygiene",
]


# ILP-based allocation with new egalitarian formulation including drivers and food types
def egalitarianILP(donors, agencies, adjMatrix, drivers=None, use_gurobi=False):

    print(f"\n{'='*60}")
    print("STARTING NEW ILP SOLVER - EGALITARIAN + EGALITARIAN ACROSS FOOD TYPES")
    print(f"{'='*60}")

    # use default drivers if none provided
    if drivers is None:
        from driver import generateDrivers

        drivers = generateDrivers(5)

    # calculate agency weights (meals served per week, use median if missing)
    agencyWeights = calculateAgencyWeights(agencies)

    # create qgf matrix: quantity of food type f in item g
    qgfMatrix = createFoodTypeMatrix(donors)

    # create 3D feasibility matrix showing which drivers can make which trips
    feasibilityMatrix = createDriverFeasibilityMatrix(
        donors, agencies, drivers, adjMatrix
    )

    # time step limit
    timeSteps = [0, 1, 2, 3, 4, 6, 7, 8, 9]

    # create the optimization model
    model = plp.LpProblem("Food_Allocation_New_Egalitarian", plp.LpMaximize)

    # decision variables
    # xi_g: binary indicating if item g is assigned to agency i
    x = {}
    for agencyIdx in range(len(agencies)):
        for donorIdx, donor in enumerate(donors):
            for itemIdx in range(len(donor.items)):
                varName = f"x_a{agencyIdx}_d{donorIdx}_i{itemIdx}"
                x[(agencyIdx, donorIdx, itemIdx)] = plp.LpVariable(
                    varName, cat="Binary"
                )

    # yt_i_d_k: binary indicating trip from donor d to agency i by driver k at time t
    y = {}
    for t in timeSteps:
        for agencyIdx in range(len(agencies)):
            for donorIdx in range(len(donors)):
                for driverIdx in range(len(drivers)):
                    varName = f"y_t{t}_a{agencyIdx}_d{donorIdx}_k{driverIdx}"
                    y[(t, agencyIdx, donorIdx, driverIdx)] = plp.LpVariable(
                        varName, cat="Binary"
                    )

    # r: minimum weighted utility across all agencies
    r = plp.LpVariable("r", lowBound=0)

    # rf: minimum weighted utility per food type across all agencies
    rf = {}
    for foodType in FOOD_TYPES:
        rf[foodType] = plp.LpVariable(f"r_{foodType}", lowBound=0)

    print(f"Created {len(x)} allocation variables and {len(y)} trip variables")

    # objective: maximize minimum weighted utility (with food type weighting)
    # for now, give equal weight (α=1) to all food types
    alphaWeights = {foodType: 1.0 for foodType in FOOD_TYPES}

    model += (
        r + plp.lpSum(alphaWeights[foodType] * rf[foodType] for foodType in FOOD_TYPES),
        "Maximize_Min_Weighted_Utility",
    )

    # constraint 1: minimum food per person served constraint
    for agencyIdx in range(len(agencies)):
        totalFoodReceived = plp.lpSum(
            qgfMatrix[(donorIdx, itemIdx, foodType)] * x[(agencyIdx, donorIdx, itemIdx)]
            for donorIdx, donor in enumerate(donors)
            for itemIdx in range(len(donor.items))
            for foodType in FOOD_TYPES
        )

        model += (
            totalFoodReceived >= r * agencyWeights[agencyIdx],
            f"MinFoodPerPerson_a{agencyIdx}",
        )

    # constraint 2: minimum food per person served per food type
    for agencyIdx in range(len(agencies)):
        for foodType in FOOD_TYPES:
            foodTypeReceived = plp.lpSum(
                qgfMatrix[(donorIdx, itemIdx, foodType)]
                * x[(agencyIdx, donorIdx, itemIdx)]
                for donorIdx, donor in enumerate(donors)
                for itemIdx in range(len(donor.items))
            )

            model += (
                foodTypeReceived >= rf[foodType] * agencyWeights[agencyIdx],
                f"MinFoodPerPersonPerType_a{agencyIdx}_f{foodType}",
            )

    # constraint 3: each item allocated at most once
    for donorIdx, donor in enumerate(donors):
        for itemIdx in range(len(donor.items)):
            model += (
                plp.lpSum(
                    x[(agencyIdx, donorIdx, itemIdx)]
                    for agencyIdx in range(len(agencies))
                )
                <= 1,
                f"ItemOnce_d{donorIdx}_i{itemIdx}",
            )

    # constraint 4: each driver does at most one trip per time step
    for t in timeSteps:
        for driverIdx in range(len(drivers)):
            model += (
                plp.lpSum(
                    y[(t, agencyIdx, donorIdx, driverIdx)]
                    for agencyIdx in range(len(agencies))
                    for donorIdx in range(len(donors))
                )
                <= 1,
                f"DriverOneTrip_t{t}_k{driverIdx}",
            )

    # constraint 5: at most one driver per trip per time step
    for t in timeSteps:
        for agencyIdx in range(len(agencies)):
            for donorIdx in range(len(donors)):
                model += (
                    plp.lpSum(
                        y[(t, agencyIdx, donorIdx, driverIdx)]
                        for driverIdx in range(len(drivers))
                    )
                    <= 1,
                    f"OneDrierPerTrip_t{t}_a{agencyIdx}_d{donorIdx}",
                )

    # constraint 6: only feasible trips (based on driver capabilities and adjacency)
    feasibleTripsAdded = 0
    for t in timeSteps:
        for agencyIdx in range(len(agencies)):
            for donorIdx in range(len(donors)):
                for driverIdx in range(len(drivers)):
                    if not feasibilityMatrix[agencyIdx][donorIdx][driverIdx]:
                        model += (
                            y[(t, agencyIdx, donorIdx, driverIdx)] == 0,
                            f"InfeasibleTrip_t{t}_a{agencyIdx}_d{donorIdx}_k{driverIdx}",
                        )
                        feasibleTripsAdded += 1

    print(f"Added {feasibleTripsAdded} infeasible trip constraints")

    # constraint 7: items can only be assigned if corresponding trip exists
    for agencyIdx in range(len(agencies)):
        for donorIdx, donor in enumerate(donors):
            for itemIdx in range(len(donor.items)):
                # item can only be assigned if there's a trip from donor to agency
                # ? Does the time step matter here?
                model += (
                    x[(agencyIdx, donorIdx, itemIdx)]
                    <= plp.lpSum(
                        y[(t, agencyIdx, donorIdx, driverIdx)]
                        for t in timeSteps
                        for driverIdx in range(len(drivers))
                    ),
                    f"ItemRequiresTrip_a{agencyIdx}_d{donorIdx}_i{itemIdx}",
                )

    # solve the ILP
    print(f"\nSolving new ILP optimization problem...")

    if use_gurobi:
        solver = plp.GUROBI_CMD(msg=1, timeLimit=300)
    else:
        solver = plp.PULP_CBC_CMD(msg=1, timeLimit=300)  # 5 minute time limit

    model.solve(solver)

    print(f"\n{'='*60}")
    print(f"ILP Solution Status: {plp.LpStatus[model.status]}")

    if model.status == plp.LpStatusOptimal:
        print(f"Optimal Equalitarian Welfare: {r.varValue:.3f}")
        for foodType in FOOD_TYPES:
            print(f"  Min {foodType}: {rf[foodType].varValue:.3f}")
    elif model.status == plp.LpStatusNotSolved:
        print("WARNING: Problem not solved - check constraints")
        return defaultdict(list), [0.0] * len(agencies)
    elif model.status == plp.LpStatusInfeasible:
        print("WARNING: Problem is infeasible - check constraints")
        return defaultdict(list), [0.0] * len(agencies)

    print(f"{'='*60}\n")

    # extract solution
    allocation = defaultdict(list)
    agencyUtilities = [0.0] * len(agencies)

    # extract allocation results
    for (agencyIdx, donorIdx, itemIdx), var in x.items():
        if var.varValue and var.varValue > 0.5:  # check if allocated
            allocation[agencyIdx].append((donorIdx, itemIdx))
            item = donors[donorIdx].items[itemIdx]
            agencyUtilities[agencyIdx] += item.weight

    return allocation, agencyUtilities


# calculates agency weights (meals served per week)
def calculateAgencyWeights(agencies):
    weights = []

    # debug: check if we have any agencies
    if not agencies:
        print("ERROR: No agencies provided to calculateAgencyWeights")
        return [100.0]  # return default weight

    print(f"Processing {len(agencies)} agencies for weight calculation")

    # collect all valid weights
    validWeights = []
    for agency in agencies:
        if (
            hasattr(agency, "servedPerWk")
            and agency.servedPerWk
            and agency.servedPerWk > 0
        ):
            validWeights.append(agency.servedPerWk)
        else:
            print(
                f"Agency {agency.name} has invalid servedPerWk: {getattr(agency, 'servedPerWk', 'None')}"
            )

    print(f"Found {len(validWeights)} agencies with valid weight data")

    # calculate median for missing values
    if validWeights:
        medianWeight = statistics.median(validWeights)
        print(f"Calculated median weight: {medianWeight}")
    else:
        medianWeight = 100  # default fallback
        print(f"No valid weights found, using default median: {medianWeight}")

    # assign weights
    for agency in agencies:
        if (
            hasattr(agency, "servedPerWk")
            and agency.servedPerWk
            and agency.servedPerWk > 0
        ):
            weights.append(agency.servedPerWk)
        else:
            weights.append(medianWeight)
            print(f"Using median weight {medianWeight} for agency {agency.name}")

    # ensure weights list is not empty
    if not weights:
        print("ERROR: weights list is still empty, using default weights")
        weights = [medianWeight] * len(agencies)

    print(f"Final weights list length: {len(weights)}")
    print(
        f"Agency weights: min={min(weights):.1f}, max={max(weights):.1f}, median={medianWeight:.1f}"
    )
    return weights


# creates the qgf matrix: quantity of food type f in item g
def createFoodTypeMatrix(donors):
    qgf = {}

    for donorIdx, donor in enumerate(donors):
        for itemIdx, item in enumerate(donor.items):
            for foodType in FOOD_TYPES:
                # get quantity of this food type in this item
                quantity = item.foodTypeQuantities.get(foodType, 0.0)
                qgf[(donorIdx, itemIdx, foodType)] = quantity

    return qgf


# creates for driver-donor-agency combinations
def createDriverFeasibilityMatrix(donors, agencies, drivers, adjMatrix):
    # 3D feasibility matrix: feasible[agency][donor][driver]
    # True if driver can make trip from donor to agency
    feasible = np.zeros((len(agencies), len(donors), len(drivers)), dtype=bool)

    for agencyIdx in range(len(agencies)):
        for donorIdx in range(len(donors)):
            for driverIdx in range(len(drivers)):
                # check if donor-agency connection exists in adjacency matrix
                if adjMatrix[donorIdx][agencyIdx] == 1:
                    # for now, assume all drivers can make all feasible trips
                    # TODO check driver location, capacity, etc.
                    feasible[agencyIdx][donorIdx][driverIdx] = True

    totalFeasible = np.sum(feasible)
    print(
        f"Created driver feasibility matrix: {totalFeasible} feasible trips out of {feasible.size} possible"
    )

    return feasible


# randomly assigns food types to items (1-3 types per item)
def randItemGen(donors, minItems=1, maxItems=5, minWeight=5, maxWeight=20, seed=None):

    if seed is not None:
        random.seed(seed)

    for donor in donors:
        numItems = random.randint(minItems, maxItems)
        donor.items = []  # clear existing items

        for i in range(numItems):
            weight = random.randint(minWeight, maxWeight)
            item = Item(None, weight)  # generic food type

            # randomly assign 1-3 food types
            numFoodTypes = random.randint(1, 3)
            selectedFoodTypes = random.sample(FOOD_TYPES, numFoodTypes)

            # distribute weight equally among selected food types
            weightPerType = weight / numFoodTypes

            for foodType in selectedFoodTypes:
                item.foodTypeQuantities[foodType] = weightPerType

            donor.items.append(item)

    totalItems = sum(len(donor.items) for donor in donors)
    totalWeight = sum(sum(item.weight for item in donor.items) for donor in donors)

    print(
        f"Randomly generated {totalItems} items totaling {totalWeight}lbs across {len(donors)} donors"
    )
    print(f"Food types assigned: {FOOD_TYPES}")


# prints a summary of the allocation results
def printAllocationSummary(allocation, agencies, donors, agencyUtilities):
    print("\n" + "=" * 50)
    print("ALLOCATION SUMMARY")
    print("=" * 50)

    totalAllocated = 0
    allocatedAgencies = 0
    totalTrips = 0

    for agencyIdx, allocatedItems in allocation.items():
        if len(allocatedItems) > 0:
            agency = agencies[agencyIdx]
            utility = agencyUtilities[agencyIdx]
            utilityPerPerson = (
                utility / agency.servedPerWk if agency.servedPerWk > 0 else 0
            )

            print(f"{agency.name}:")
            print(f"  Total food: {utility:.1f}lbs")
            print(f"  People served/wk: {agency.servedPerWk}")
            print(f"  Per person served: {utilityPerPerson:.3f}lbs")
            print(f"  Items received: {len(allocatedItems)}")

            # group items by donor to show trip details
            donorToWeight = {}
            donorToItemCount = {}

            for donorIdx, itemIdx in allocatedItems:
                item = donors[donorIdx].items[itemIdx]
                donorName = donors[donorIdx].name

                if donorName not in donorToWeight:
                    donorToWeight[donorName] = 0
                    donorToItemCount[donorName] = 0

                donorToWeight[donorName] += item.weight
                donorToItemCount[donorName] += 1

            # display trip details
            print(f"  Trips received from {len(donorToWeight)} donors:")
            for donorName in sorted(donorToWeight.keys()):
                totalWeight = donorToWeight[donorName]
                itemCount = donorToItemCount[donorName]
                print(f"    • {donorName}: {totalWeight:.1f}lbs ({itemCount} items)")
                totalTrips += 1

            print()  # blank line between agencies
            totalAllocated += utility
            allocatedAgencies += 1

    print(f"Total agencies receiving food: {allocatedAgencies}/{len(agencies)}")
    print(f"Total food allocated: {totalAllocated:.1f}lbs")
    print(f"Total unique donor-to-agency trips: {totalTrips}")

    # calculate fairness metrics
    utilitiesPerPerson = []
    for agencyIdx in range(len(agencies)):
        if agencies[agencyIdx].servedPerWk and agencies[agencyIdx].servedPerWk > 0:
            utilityPerPerson = (
                agencyUtilities[agencyIdx] / agencies[agencyIdx].servedPerWk
            )
            utilitiesPerPerson.append(utilityPerPerson)

    if utilitiesPerPerson:
        minUtility = min(utilitiesPerPerson)
        maxUtility = max(utilitiesPerPerson)
        avgUtility = sum(utilitiesPerPerson) / len(utilitiesPerPerson)

        print(f"\nFairness Metrics (lbs per person served):")
        print(f"  Minimum: {minUtility:.3f}")
        print(f"  Maximum: {maxUtility:.3f}")
        print(f"  Average: {avgUtility:.3f}")
        print(f"  Range: {maxUtility - minUtility:.3f}")
