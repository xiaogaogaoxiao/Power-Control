import matplotlib.pyplot as plt
import numpy as np
import cvxpy as cp

class Het_Network():
    def __init__(self, num_femto_cells, num_macro_users, max_users, max_antennas, interference_threshold):
        """
        TODO Enforce players have more antennas than users
        :param num_femto_cells:
        :param num_macro_users:
        :param max_users:
        :param max_antennas:
        :param interference_threshold:
        """
        self.coverage_area = (100, 100)
        self.base_stations = []
        # these loops should probably be moved out of the constructor
        [self.base_stations.append(Femto_Base_Station(i, self, np.random.randint(1, max_users+1)
                                                      , np.random.randint(1, max_antennas+1))) for i in range(num_femto_cells)]

        self.macro_users = []
        [self.macro_users.append(Macro_User(i, self, interference_threshold)) for i in range(num_macro_users)]
        self.update_macro_cells()
        self.setup_base_stations()

        print("test")

    def get_network_channels(self):
        """

        :return: A list of the base stations and their downlink channels as two lists. The first as the channels to users
        and the second as channels to the macro users they interfere with.
        """
        ret = dict()
        for station in self.base_stations:
            station_l = dict()
            station_l["macro"] = station.get_macro_channel_matrices()
            station_l["femto"] = station.get_user_channel_matrices()
            ret[str(station.ID)] = station_l
        return ret

    def get_power_constaints(self):
        constaints = dict()
        for station in self.base_stations:
            constaints[str(station.ID)] = station.power_constaint
        return constaints

    def get_beam_formers(self):
        beam_formers = []
        for base_station in self.base_stations:
            beam_formers.append(base_station.beam_forming_matrix)
        return beam_formers

    def get_macro_matrices(self):
        ret = dict()
        for macro in self.macro_users:
            ret[str(macro.ID)] = macro.downlink_channels
        return ret

    def get_macro_thresholds(self):
        thresholds = dict()
        for macro in self.macro_users:
            thresholds[str(macro.ID)] = macro.interference_threshold
        return thresholds

    def get_femto_cells(self):
        return self.base_stations

    def allocate_power_step(self, num_iterations):
        for i in range(num_iterations):
            [player.solve_local_opimization() for player in self.base_stations]
            self.__update_dual_variables()

    def __update_dual_variables(self):
        """
        Update all dual variables in the distributed optimization problem
        :return:
        """
        # First update the dual variables of the macro users
        [macro_user.update_dual_variabls() for macro_user in self.macro_users]
        # Second update the dual variables for the other constaints (Note this order doesn't matter)
        #TODO UPDATE


    def update_macro_cells(self):
        for cell in self.base_stations:
            cell.reconize_macro_user(self.macro_users)

    def setup_base_stations(self):
        self.central_utility_function = 0
        for base_station in self.base_stations:
            base_station.setup_users()
            base_station.setup_utility()
            self.central_utility_function += base_station.utility_function
        self.central_utility_function = cp.sum(self.central_utility_function)

    def move_femto_users(self):
        for cell in self.base_stations:
            cell.move_users()
        return None

    def move_macro_users(self):
        return None

    def get_station_locations(self):
        locations = []
        for station in self.base_stations:
            locations.append(station.location)
        locations = np.asarray(locations)
        return locations

    def get_macro_locations(self):
        locations = []
        for user in self.macro_users:
            locations.append(user.location)
        locations = np.asarray(locations)
        return locations

    def print_layout(self):
        bs_locations = self.get_station_locations()
        plt.scatter(bs_locations[:,0],bs_locations[:,1],marker='H')
        mu_locations = self.get_macro_locations()
        plt.scatter(mu_locations[:,0],mu_locations[:,1],marker='x')
        plt.show()


class Femto_Base_Station():
    def __init__(self, ID, network, num_femto_users, num_antenna,utility_function=np.sum):
        self.ID = ID
        self.users = []
        # Ensure there are always more antennas than users
        self.number_antennas = num_antenna+num_femto_users
        self.macro_users = []
        self.network = network
        self.location = self.setup_location()
        self.coverage_size = np.array((5, 5))
        self.connect_users(num_femto_users)
        self.beam_forming_matrix = cp.Variable((self.number_antennas, num_femto_users), complex=True)
        self.power_constaint = 1
        self.utility_function = utility_function

    #TODO type this parameter as macro user
    def setup_utility(self):
        self.utility_function = self.utility_function(self.get_user_sinr())
        pass

    def reconize_macro_user(self, users):
        for macro_user in users:
            self.macro_users.append(macro_user)
            macro_user.add_interferer(self)

    def connect_users(self, num_femto_users):
        for ind in range(num_femto_users):
            new_user = Femto_User(ind, self.network, self)
            self.users.append(new_user)

    def setup_users(self):
        for user in self.users:
            user.setup_channels()

    def get_user_channel_matrices(self):
        downlink = []
        for m_user in self.users:
            downlink.append(m_user.get_channel_for_base_station(self.ID))
        downlink = np.asarray(downlink)
        return downlink

    def get_macro_channel_matrices(self):
        downlink = []
        for m_user in self.macro_users:
            downlink.append(m_user.get_channel_for_base_station(self.ID))
        downlink = np.asarray(downlink)
        return downlink

    def getID(self):
        return self.ID

    def move_femto_users(self):
        for user in self.users:
            user.move()

    def setup_location(self):
        return np.array((np.random.randint(0,self.network.coverage_area[0]), np.random.randint(0,self.network.coverage_area[1])))

    def get_user_sinr(self):
        all_sinr = []
        for ind, user in enumerate(self.users):
            beam = self.beam_forming_matrix[:,ind]
            channel = user.get_channel_for_base_station(self.ID)
            all_sinr.append(cp.log(beam.H@channel*channel.conj().T@beam))
        return all_sinr

    def solve_local_opimization(self):
        # The distributed dual of the potential game
        g_x_lambda = self.utility_function
        cp.Minimize(g_x_lambda)


class User:
    def __init__(self, ID, network):
        self.ID = ID
        self.uplink_channels = dict()
        self.downlink_channels = dict()
        self.location = (0, 0)
        self.network = network
        self.move()

    def get_channel_for_base_station(self, base_station_index):
        return self.downlink_channels.get(str(base_station_index))

    def move(self):
        for link in self.uplink_channels:
            link = np.random.randn()
        for link in self.downlink_channels:
            link = np.random.randn()
        self.location = (np.random.randint(self.network.coverage_area[0]), np.random.randint(self.network.coverage_area[0]))


class Macro_User(User):
    def __init__(self, ID, network,interference_threshold):
        User.__init__(self, ID, network)
        self.interference = 0
        self.interference_threshold = interference_threshold

    def add_interferer(self, interferer :Femto_Base_Station):
        self.downlink_channels[str(interferer.ID)] = np.random.randn(interferer.number_antennas)

    def update_dual_variabls(self):
        pass



class Femto_User(User):
    def __init__(self, ID, network, parent, sigma_square=1):
        """
        For now assume that the femto users are only single antenna
        :param ID:
        :param parent:
        :param sigma_square:
        """
        User.__init__(self, ID, network)
        self.parent = parent
        self.power_from_base_station = 0
        self.interference = 0
        self.noise_power = sigma_square

    def setup_channels(self):
        for base_station in self.network.base_stations:
            self.downlink_channels[str(base_station.ID)] = np.random.randn(base_station.number_antennas)

    def update_power(self, power):
        self.power_from_base_station = power
        self.SINR = self.get_sinr()

    def get_sinr(self):
        channel = self.downlink_channels[str(self.parent.getID())]
        self.SINR = channel/(self.noise_power+self.interference)
