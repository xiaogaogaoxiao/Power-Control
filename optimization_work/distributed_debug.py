from network_simulations import het_net
import cvxpy as cp
import matplotlib.pyplot as plt
import numpy as np
import copy

"""
first setup the network according using the het_net class then consolidate all of the information from the network to solve the central optimization problem
"""

def test_dist_debug():
    num_users = 10
    num_antenna = num_users + 5
    network = het_net.Het_Network(5, 30, num_users, num_antenna, .1, 1000, power_vector_setup=True)
    # network.update_beam_formers()
    for_comp = copy.deepcopy(network)
    for_comp.change_power_limit(10000)
    for_comp.update_beam_formers()
    # Choose number of iterations to allow
    num_iterations = 300
    utilities, duals = network.allocate_power_step(num_iterations)
    test_utilities, test_duals = for_comp.allocate_power_step(num_iterations)


    plt.figure()
    duals = np.asarray(duals)
    for columns in range(duals.shape[1]):
        plt.plot(duals[:, columns])

    plt.figure()
    test_duals = np.asarray(test_duals)
    labels = ["int","power"]
    for columns in range(test_duals.shape[1]):
        plt.plot(test_duals[:, columns], label=labels[columns])
        plt.legend(loc="lower left")

    network.print_layout()
    plt.figure()
    plt.plot(np.arange(num_iterations + 1), utilities, label="base")
    plt.plot(np.arange(num_iterations + 1), test_utilities, label="comparison")
    plt.legend(loc="lower left")

    plt.show()

