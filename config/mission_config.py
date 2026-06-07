"""
mission_config.py - Enclosure geometry, mesh resolution, and mission profile.

R_int : internal radius [m]      L_int : internal height [m]
L_wall: side-wall thickness [m]  L_cap : end-cap thickness [m]
R_box : outer radius   = R_int + L_wall
L_box : outer height   = L_int + 2*L_cap
"""

import numpy as np

R_int  = 0.080
L_int  = 0.250
L_wall = 0.030
L_cap  = 0.030
R_box  = R_int + L_wall
L_box  = L_int + 2.0 * L_cap

Nr = 32
Nz = 100
N_wall = 5

dt         = 30.0
t_ascent   = 6600.0
t_float    = 0.0
t_descent  = 6000.0
t_end      = 6800.0
save_every = 2

h_inside = 1.5

T_launch = 298.15

_ascent_rate  = 5.0
_burst_alt    = 33_000.0
_descent_rate = 5.5


def h_alt_fn(t: float) -> float:
    """Altitude [m] vs time [s]: linear ascent to burst apogee, then descent."""
    if t <= t_ascent:
        return _ascent_rate * t
    return max(0.0, _burst_alt - _descent_rate * (t - t_ascent))


def V_rel_fn(t: float) -> float:
    """Gondola speed relative to the air [m/s]."""
    if t <= t_ascent:
        return _ascent_rate
    return _descent_rate


MISSION_CONFIG = {
    'R_box': R_box, 'L_box': L_box,
    'L_wall': L_wall, 'L_cap': L_cap,
    'R_int': R_int, 'L_int': L_int,
    'Nr': Nr, 'Nz': Nz, 'N_wall': N_wall,
    'dt': dt, 't_end': t_end, 'save_every': save_every,
    'h_inside': h_inside,
    'T_launch': T_launch,
    'h_alt_fn': h_alt_fn,
    'V_rel_fn': V_rel_fn,
}
