import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import time

# takes an m x n adjacency matrix and visualizes it as a bipartite graph
def plotBipartiteGraph(adjacencyMatrix, donorLabels=None, agencyLabels=None, figureSize=(15, 11)):

    # adjacencyMatrix: 2D array/list representing the bipartite graph
    # donorLabels: list of labels for food donors (optional)
    # agencyLabels: list of labels for food recipient agencies (optional)
    # figureSize: tuple specifying the figure size (width, height)
    
    # convert to numpy array for easier handling
    adjMatrix = np.array(adjacencyMatrix)
    numDonors, numAgencies = adjMatrix.shape
    
    # create default labels if none provided
    if donorLabels is None:
        donorLabels = [f"Donor_{i+1}" for i in range(numDonors)]
    if agencyLabels is None:
        agencyLabels = [f"Agency_{i+1}" for i in range(numAgencies)]
    
    # create bipartite graph
    bipartiteGraph = nx.Graph()
    
    # add donor nodes (left side)
    donorNodes = [f"D_{i}" for i in range(numDonors)]
    bipartiteGraph.add_nodes_from(donorNodes, bipartite=0)
    
    # add agency nodes (right side)
    agencyNodes = [f"A_{i}" for i in range(numAgencies)]
    bipartiteGraph.add_nodes_from(agencyNodes, bipartite=1)
    
    # add edges based on adjacency matrix
    for donorIdx in range(numDonors):
        for agencyIdx in range(numAgencies):
            if adjMatrix[donorIdx][agencyIdx] == 1:
                bipartiteGraph.add_edge(f"D_{donorIdx}", f"A_{agencyIdx}")
    
    # create layout for bipartite graph
    donorPositions = {f"D_{i}": (0, i) for i in range(numDonors)}
    agencyPositions = {f"A_{i}": (2, i) for i in range(numAgencies)}
    nodePositions = {**donorPositions, **agencyPositions}
    
    # create the plot
    plt.figure(figsize=figureSize)
    
    # draw donor nodes (left side)
    nx.draw_networkx_nodes(bipartiteGraph, nodePositions, 
                          nodelist=donorNodes, 
                          node_color='lightblue', 
                          node_size=1000, 
                          alpha=0.8)
    
    # draw agency nodes (right side)
    nx.draw_networkx_nodes(bipartiteGraph, nodePositions, 
                          nodelist=agencyNodes, 
                          node_color='lightcoral', 
                          node_size=1000, 
                          alpha=0.8)
    
    # draw edges
    nx.draw_networkx_edges(bipartiteGraph, nodePositions, 
                          edge_color='gray', 
                          width=2, 
                          alpha=0.6)
    
    # create labels for display
    displayLabels = {}
    for i, donorNode in enumerate(donorNodes):
        displayLabels[donorNode] = donorLabels[i]
    for i, agencyNode in enumerate(agencyNodes):
        displayLabels[agencyNode] = agencyLabels[i]
    
    # draw labels
    nx.draw_networkx_labels(bipartiteGraph, nodePositions, 
                           labels=displayLabels, 
                           font_size=10, 
                           font_weight='bold')
    
    # customize the plot
    plt.title("Bipartite Graph of Donors to Agencies", 
              fontsize=16, fontweight='bold', pad=20)
    plt.text(0, max(numDonors, numAgencies) + 0.5, "Food Donors", 
             fontsize=14, fontweight='bold', ha='center')
    plt.text(2, max(numDonors, numAgencies) + 0.5, "Recieving Agencies", 
             fontsize=14, fontweight='bold', ha='center')
    
    # remove axes
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    # print summary statistics
    totalConnections = np.sum(adjMatrix)
    print(f"\nBipartite Graph Summary:")
    print(f"Number of Food Donors: {numDonors}")
    print(f"Number of Recipient Agencies: {numAgencies}")
    print(f"Total Connections: {totalConnections}")
    print(f"Connection Density: {totalConnections / (numDonors * numAgencies):.2%}")



# creates adjacency matrix showing only edges used in allocation
def createAllocationMatrix(allocation, numDonors, numAgencies):
    """
    creates an adjacency matrix showing only the donor-agency connections
    that were actually used in the allocation
    
    allocation: dict where allocation[agencyIdx] = list of (donorIdx, itemIdx) tuples
    numDonors: total number of donors
    numAgencies: total number of agencies
    
    returns: numpy array representing used connections
    """
    
    allocationMatrix = np.zeros((numDonors, numAgencies))
    
    for agencyIdx, allocatedItems in allocation.items():
        for donorIdx, itemIdx in allocatedItems:
            allocationMatrix[donorIdx][agencyIdx] = 1
    
    return allocationMatrix


# plots bipartite graph showing only edges used in allocation
def plotAllocationGraph(allocation, donors, agencies, donorLabels=None, agencyLabels=None, figureSize=(15, 11)):
    """
    visualizes the bipartite graph showing only the donor-agency connections
    that were actually used in the food allocation
    
    allocation: dict where allocation[agencyIdx] = list of (donorIdx, itemIdx) tuples
    donors: list of donor objects
    agencies: list of agency objects
    donorLabels: optional list of donor labels
    agencyLabels: optional list of agency labels
    figureSize: tuple specifying figure size
    """
    
    # create allocation matrix
    allocationMatrix = createAllocationMatrix(allocation, len(donors), len(agencies))
    
    # use existing labels or create defaults
    if donorLabels is None:
        donorLabels = [donor.name for donor in donors]
    if agencyLabels is None:
        agencyLabels = [agency.name for agency in agencies]
    
    # create the graph
    numDonors, numAgencies = allocationMatrix.shape
    bipartiteGraph = nx.Graph()
    
    # add donor nodes (left side)
    donorNodes = [f"D_{i}" for i in range(numDonors)]
    bipartiteGraph.add_nodes_from(donorNodes, bipartite=0)
    
    # add agency nodes (right side)
    agencyNodes = [f"A_{i}" for i in range(numAgencies)]
    bipartiteGraph.add_nodes_from(agencyNodes, bipartite=1)
    
    # add edges based on allocation matrix
    usedEdges = []
    for donorIdx in range(numDonors):
        for agencyIdx in range(numAgencies):
            if allocationMatrix[donorIdx][agencyIdx] == 1:
                bipartiteGraph.add_edge(f"D_{donorIdx}", f"A_{agencyIdx}")
                usedEdges.append((f"D_{donorIdx}", f"A_{agencyIdx}"))
    
    # create layout for bipartite graph
    donorPositions = {f"D_{i}": (0, i) for i in range(numDonors)}
    agencyPositions = {f"A_{i}": (2, i) for i in range(numAgencies)}
    nodePositions = {**donorPositions, **agencyPositions}
    
    # create the plot
    plt.figure(figsize=figureSize)
    
    # draw all donor nodes (including those not used)
    nx.draw_networkx_nodes(bipartiteGraph, nodePositions, 
                          nodelist=donorNodes, 
                          node_color='lightblue', 
                          node_size=1000, 
                          alpha=0.8)
    
    # draw all agency nodes (including those not used)
    nx.draw_networkx_nodes(bipartiteGraph, nodePositions, 
                          nodelist=agencyNodes, 
                          node_color='lightcoral', 
                          node_size=1000, 
                          alpha=0.8)
    
    # highlight used edges in green with thicker lines
    if usedEdges:
        nx.draw_networkx_edges(bipartiteGraph, nodePositions, 
                              edgelist=usedEdges,
                              edge_color='green', 
                              width=3, 
                              alpha=0.8)
    
    # create labels for display
    displayLabels = {}
    for i, donorNode in enumerate(donorNodes):
        displayLabels[donorNode] = donorLabels[i]
    for i, agencyNode in enumerate(agencyNodes):
        displayLabels[agencyNode] = agencyLabels[i]
    
    # draw labels
    nx.draw_networkx_labels(bipartiteGraph, nodePositions, 
                           labels=displayLabels, 
                           font_size=8, 
                           font_weight='bold')
    
    # customize the plot
    plt.title("Food Allocation Results: Actual Donor-Agency Transfers", 
              fontsize=16, fontweight='bold', pad=20)
    plt.text(0, max(numDonors, numAgencies) + 0.5, "Food Donors", 
             fontsize=14, fontweight='bold', ha='center')
    plt.text(2, max(numDonors, numAgencies) + 0.5, "Receiving Agencies", 
             fontsize=14, fontweight='bold', ha='center')
    
    # add legend
    from matplotlib.lines import Line2D
    legendElements = [Line2D([0], [0], color='green', lw=3, label='Food Transferred')]
    plt.legend(handles=legendElements, loc='upper right')
    
    # remove axes
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    # print allocation summary statistics
    totalTransfers = np.sum(allocationMatrix)
    donorsUsed = np.sum(np.any(allocationMatrix, axis=1))
    agenciesServed = np.sum(np.any(allocationMatrix, axis=0))
    
    print(f"\nAllocation Graph Summary:")
    print(f"Total Donor-Agency Transfers: {int(totalTransfers)}")
    print(f"Donors Used: {int(donorsUsed)}/{numDonors}")
    print(f"Agencies Served: {int(agenciesServed)}/{numAgencies}")
    print(f"Donor Utilization: {donorsUsed/numDonors:.1%}")
    print(f"Agency Coverage: {agenciesServed/numAgencies:.1%}")


# plots both the full network and allocation side by side
def plotComparisonGraphs(fullAdjMatrix, allocation, donors, agencies, 
                        donorLabels=None, agencyLabels=None, figureSize=(20, 10)):
    """
    creates side-by-side comparison of full donor-agency network vs actual allocation
    
    fullAdjMatrix: original adjacency matrix showing all possible connections
    allocation: dict where allocation[agencyIdx] = list of (donorIdx, itemIdx) tuples
    donors: list of donor objects
    agencies: list of agency objects
    donorLabels: optional list of donor labels
    agencyLabels: optional list of agency labels
    figureSize: tuple specifying figure size
    """
    
    # create allocation matrix
    allocationMatrix = createAllocationMatrix(allocation, len(donors), len(agencies))
    
    # use existing labels or create defaults
    if donorLabels is None:
        donorLabels = [donor.name for donor in donors]
    if agencyLabels is None:
        agencyLabels = [agency.name for agency in agencies]
    
    # create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figureSize)
    
    # plot 1: full network
    numDonors, numAgencies = fullAdjMatrix.shape
    
    for i in range(numDonors):
        for j in range(numAgencies):
            if fullAdjMatrix[i][j] == 1:
                ax1.plot([0, 1], [i, j], 'gray', alpha=0.2, linewidth=0.5)
    
    ax1.scatter([0] * numDonors, range(numDonors), c='lightblue', s=80, zorder=3)
    ax1.scatter([1] * numAgencies, range(numAgencies), c='lightcoral', s=80, zorder=3)
    
    ax1.set_xlim(-0.1, 1.1)
    ax1.set_ylim(-1, max(numDonors, numAgencies))
    ax1.set_title("Full Donor-Agency Network\n(All Possible Connections)", 
                  fontsize=12, fontweight='bold')
    ax1.text(0, -0.5, 'Donors', ha='center', fontsize=10, fontweight='bold')
    ax1.text(1, -0.5, 'Agencies', ha='center', fontsize=10, fontweight='bold')
    ax1.axis('off')
    
    # plot 2: allocation results
    for i in range(numDonors):
        for j in range(numAgencies):
            if allocationMatrix[i][j] == 1:
                ax2.plot([0, 1], [i, j], 'green', alpha=0.8, linewidth=2)
    
    ax2.scatter([0] * numDonors, range(numDonors), c='lightblue', s=80, zorder=3)
    ax2.scatter([1] * numAgencies, range(numAgencies), c='lightcoral', s=80, zorder=3)
    
    ax2.set_xlim(-0.1, 1.1)
    ax2.set_ylim(-1, max(numDonors, numAgencies))
    ax2.set_title("Allocation Results\n(Actual Food Transfers)", 
                  fontsize=12, fontweight='bold')
    ax2.text(0, -0.5, 'Donors', ha='center', fontsize=10, fontweight='bold')
    ax2.text(1, -0.5, 'Agencies', ha='center', fontsize=10, fontweight='bold')
    ax2.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # print comparison statistics
    totalPossible = np.sum(fullAdjMatrix)
    totalUsed = np.sum(allocationMatrix)
    
    print(f"\nComparison Summary:")
    print(f"Possible connections: {int(totalPossible)}")
    print(f"Connections used: {int(totalUsed)}")
    print(f"Network utilization: {totalUsed/totalPossible:.1%}")