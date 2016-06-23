import numpy as np
from numpy.random import RandomState


class Chooser(object):
    def __init__(self, seed):
        """

        :param seed:
        :return:
        """
        self.__state = RandomState(seed)

    def generate(self, a):
        """

        :param a:
        :return:
        """
        return self.__state.choice(a)


class WeightedChooserAggregator(object):
    def __init__(self, col_to_choose, col_for_weight, seed):
        """

        :param col_to_choose:
        :param col_for_weight:
        :param seed:
        :return:
        """
        self.__state = RandomState(seed)
        self.__col_to_choose = col_to_choose
        self.__col_for_weight = col_for_weight

    def update_choose_col(self, col):
        """

        :param col:
        :return:
        """
        self.__col_to_choose = col

    def update_weight_col(self, col):
        """

        :param col:
        :return:
        """
        self.__col_for_weight = col

    def generate(self, group):
        """

        :param group:
        :return:
        """
        w = group[self.__col_for_weight] / sum(group[self.__col_for_weight])
        return self.__state.choice(group[self.__col_to_choose], p=w)


class GenericGenerator(object):
    """

    """

    def __init__(self, name, gen_type, parameters, seed=None):
        """Initialise a random number generator

        :param name: string, the name (is this useful?)
        :param gen_type: string:
            - "choice"
        :param parameters: dict, see descriptions below
        :param seed: int, seed of the generator
        :return: create a random number generator of type "gen_type", with its parameters and seeded.
        """
        self.__name = name

        self.__state = RandomState(seed)

        if gen_type == "choice":
            self.__gen = self.__state.choice
            self.__parameters = {"a": parameters.get("a", 10),
                                 "size": parameters.get("size", 1),
                                 "replace": parameters.get("replace", True),
                                 "p": parameters.get("p", None)}

        if gen_type == "pareto":

            def rescale(a, size=None, m=1.):
                return (self.__state.pareto(a, size) + 1) * m

            self.__gen = rescale
            self.__parameters = {"a": parameters.get("a", 10),
                                 "size": parameters.get("size", 1),
                                 "m": parameters.get("m", 1.)}

        if gen_type == "exponential":
            self.__gen = self.__state.exponential
            self.__parameters = {"scale":parameters.get("scale",1.),
                                 "size": parameters.get("size",1)}

    def generate(self, size=None):
        """

        :param size:
        :return:
        :return:
        """
        params = self.__parameters
        if size is not None:
            params["size"] = size
        return self.__gen(**params)

    def get_name(self):
        """

        :return: string, the name of the generator
        """
        return self.__name


class TriggerGenerator(object):
    """A trigger generator takes some parameters and returns a vector of 1's and 0's, depending if the trigger
    has been released or not

    """

    def __init__(self, name, gen_type, parameters, seed=None):
        """Initialise a trigger generator

        :param name: string, the name (is this useful?)
        :param gen_type: string:
            - "choice"
        :param parameters: dict, see descriptions below
        :param seed: int, seed of the generator
        :return: create a random number generator of type "gen_type", with its parameters and seeded.
        """
        self.__name = name

        self.__state = RandomState(seed)
        self.__gen = self.__state.rand

        if gen_type == "logistic":
            def logistic(x, a, b):
                """returns the value of the logistic function 1/(1+e^-(ax+b))
                """
                the_exp = np.minimum(-(a*x+b),10.)
                return 1./(1.+np.exp(the_exp))

            self.__function = logistic
            self.__parameters = {"a":-0.01,
                                 "b":10.}

    def generate(self, x, parameters = None):
        """

        :type x: Pandas Series
        :param x:
        :type parameters: dict
        :param parameters: keys correspond to parameter values required by the function, values are either floats or
        Pandas Series of the same length as x
        :return:
        """
        params = self.__parameters
        params["x"] = x
        if parameters is not None:
            params.update(parameters)

        probs = self.__gen(len(x.index))

        return probs < self.__function(**params)

    def get_name(self):
        """

        :return: string, the name of the generator
        """
        return self.__name



class MSISDNGenerator(object):
    """

    """

    def __init__(self, name, countrycode, prefix_list, length, seed=None):
        """

        :param name: string
        :param countrycode: string
        :param prefix_list: list of strings
        :param length: int
        :param seed: int
        :return:
        """
        self.__name = name
        self.__state = RandomState(seed)

        maxnumber = 10 ** length - 1
        self.__available = np.empty([maxnumber * len(prefix_list), 2], dtype=int)
        for i in range(len(prefix_list)):
            self.__available[i * maxnumber:(i + 1) * maxnumber, 0] = np.arange(0, maxnumber, dtype=int)
            self.__available[i * maxnumber:(i + 1) * maxnumber, 1] = i

        self.__cc = countrycode
        self.__pref = prefix_list
        self.__length = length

    def get_name(self):
        """

        :return: string, the name of the generator
        """
        return self.__name

    def generate(self, size):
        """returns a list of size randomly generated msisdns.
        Those msisdns cannot be generated again from this generator

        :param size: int
        :return: numpy array
        """
        generated_entries = self.__state.choice(np.arange(0, self.__available.shape[0], dtype=int), size, False)
        msisdns = np.array(
            [self.__cc + self.__pref[self.__available[i, 1]] + str(self.__available[i, 0]).zfill(self.__length)
             for i in generated_entries])

        self.__available = np.delete(self.__available, generated_entries, axis=0)

        return msisdns
