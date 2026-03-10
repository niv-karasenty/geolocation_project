import numpy as np
from numpy.ma.core import arccos

c = 3e8
rx0 = [0, 1]
rx1 = [1, 0]

def main():
    freq = 1e6
    delta0 = 2
    delta1 = 1
    Ts = 0.001

    alpha_min, alpha_max = get_angle(freq, delta0, Ts)
    beta_min, beta_max = get_angle(freq, delta1, Ts)

    locate(alpha_min, alpha_max, beta_min, beta_max)

def get_angle(freq, delta_time, Ts):
    wavelength = c/freq
    antenna_dist = 0.5 * wavelength

    x_min = c * (delta_time - 0.5 * Ts)
    x_max = c * (delta_time + 0.5 * Ts)
    alpha_min = arccos(x_min/antenna_dist)
    alpha_max = arccos(x_max / antenna_dist)

    return alpha_min, alpha_max

def intersect():
    return None

def locate(alpha_min, alpha_max, beta_min, beta_max):
    # find intersection depending on 2 angles (vectors)

    return None

if __name__ == '__main__':
    main()

