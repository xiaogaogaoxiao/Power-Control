from network_simulations.het_net import *
import cvxpy as cp
import matplotlib.pyplot as plt
import numpy as np
import copy
import time

"""
first setup the network according using the het_net class then consolidate all of the information from the network to solve the central optimization problem
"""
pow_dual = 1
int_dual = pow_dual
pos_dual = pow_dual
num_users = 1
num_antenna = 1
userPowerList = [10, 100, 200]
num_iterations = 200
numMacroUsers = 10
numBaseStations = 5
interferenceThreshold = 1
userPower = userPowerList[0]
network = HetNet(numBaseStations, numMacroUsers, num_users, num_antenna, interferenceThreshold, int_dual, pow_dual, pos_dual,
                               userPower,
                              power_vector_setup=True,
                              random=False)
# figsize = (5, 5)
dual_check = []
dual_plot = plt.figure()
utility = dual_plot.add_subplot(1, 1, 1)
intf = dual_plot.add_subplot(3, 1, 2)
pwr = dual_plot.add_subplot(3, 1, 2)

for powerLimit in userPowerList:
    currNetwork = copy.deepcopy(network)
    currNetwork.change_power_limit(powerLimit)
    utility, intereference, power = currNetwork.allocate_power_central()
    print(f"power: {powerLimit}")
    print(utility)
    print(intereference)
    print(power)

