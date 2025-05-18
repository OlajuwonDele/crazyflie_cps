"""
A script to fly 5 Crazyflies in formation. One stays in the center and the
other four fly around it in a circle. Mainly intended to be used with the
Flow deck.
The starting positions are vital and should be oriented like this
     >
^    +    v
     <
The distance from the center to the perimeter of the circle is around 0.5 m
"""
import math
import time

import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm

# Change uris according to your setup
URI0 = 'radio://0/80/2M/E7E7E7E760'
URI1 = 'radio://0/80/2M/E7E7E7E761'

# d: diameter of circle
# z: altitude
params0 = {'d': 0.4, 'z': 0.2}
params1 = {'d': 0.4, 'z': 0.8}

uris = {
    URI0,
    URI1,

}

params = {
    URI0: [params0],
    URI1: [params1],
}


def poshold(cf, t, z):
    steps = t * 10

    for r in range(steps):
        cf.commander.send_hover_setpoint(0, 0, 0, z)
        time.sleep(0.1)



def run_sequence(scf, params):
    print("flying")
    cf = scf.cf

    # Number of setpoints sent per second
    fs = 4
    fsi = 1.0 / fs

    # Compensation for unknown error :-(
    comp = 1.3

    # Base altitude in meters
    base = 0.5

    d = params['d']
    z = params['z']

    

    poshold(cf, 2, base)

    ramp = fs * 2
    for r in range(ramp):
        cf.commander.send_hover_setpoint(0, 0, 0, base + r * (z + base) / ramp)
        time.sleep(fsi)
        

    poshold(cf, 2, z)

    for _ in range(1):

        # The time for one revolution
        circle_time = 20

        for t in range(circle_time):
            print(t)
            scale = (2 / (3 - math.cos(2*t)))
            x = 0.4 * scale * math.cos(t) 
            y =  0.4 * scale * math.sin(2*t) / 2
            cf.commander.send_position_setpoint( x, y, z, 1)
            print(x)
            print(y)
            time.sleep(1)

        circle_time = 40
        for t in range(circle_time):
            cf.commander.send_hover_setpoint(d * comp * math.pi / 8,
                                                  0, 360.0 /8 , z)
            time.sleep(fsi)

    poshold(cf, 2, z)

    for r in range(ramp):
        cf.commander.send_hover_setpoint(0, 0, 0,
                                         base + (ramp - r) * (z - base) / ramp)
        time.sleep(fsi)

    poshold(cf, 1, base)

    cf.commander.send_stop_setpoint()


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.reset_estimators()
        swarm.parallel(run_sequence, args_dict=params)