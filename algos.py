import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# takes an m x n adjacency matrix and visualizes it as a bipartite graph
def plotBipartiteGraph(adjacencyMatrix, donorLabels=None, agencyLabels=None, figureSize=(12, 8)):

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
    plt.title("Bipartite Graph: Food Donors to Recipient Agencies", 
              fontsize=16, fontweight='bold', pad=20)
    plt.text(0, max(numDonors, numAgencies) + 0.5, "Food Donors", 
             fontsize=14, fontweight='bold', ha='center')
    plt.text(2, max(numDonors, numAgencies) + 0.5, "Recipient Agencies", 
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

# example usage function
def createExampleGraph():
    """
    Creates and displays an example bipartite graph.
    """
    # example 4x5 adjacency matrix
    exampleMatrix = [
        [1, 0, 1, 0, 1],  # donor 1 connects to agencies 1, 3, 5
        [0, 1, 1, 0, 0],  # donor 2 connects to agencies 2, 3
        [1, 1, 0, 1, 0],  # donor 3 connects to agencies 1, 2, 4
        [0, 0, 1, 1, 1]   # donor 4 connects to agencies 3, 4, 5
    ]
    
    # custom labels
    donorNames = ["Restaurant A", "Grocery Store B", "Bakery C", "Farm D"]
    agencyNames = ["Food Bank 1", "Shelter 2", "Community Center", "Senior Center", "School Program"]
    
    plotBipartiteGraph(exampleMatrix, donorNames, agencyNames)

# uncomment the line below to run the example
createExampleGraph()