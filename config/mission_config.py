"""Enclosure geometry, mesh resolution, mission profile, and environment boundary
conditions.

The internal field is a 2-D planar (x, z) section of the cavity, treated as an
extruded slab of out-of-plane depth D_int. Interior dimensions describe the meshed
domain; the outer-shell dimensions (R_box, L_box) drive the external convection
calculation in Block A only.
"""

import numpy as np

# Interior cavity (planar mesh domain). R_int is the full interior x-width.
R_int  = 0.170
L_int  = 0.250
D_int  = 0.170

# Enclosure shell (external-convection geometry).
L_wall = 0.030
L_cap  = 0.030
R_box  = 0.115
L_box  = L_int + 2.0 * L_cap

Nr = 68                 # 170 mm / 68 -> 2.5 mm cells (dx = dz)
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
    """Altitude [m] vs time [s]: linear ascent to burst, then parachute descent."""
    if t <= t_ascent:
        return _ascent_rate * t
    return max(0.0, _burst_alt - _descent_rate * (t - t_ascent))


def V_rel_fn(t: float) -> float:
    """Speed relative to the air [m/s]."""
    if t <= t_ascent:
        return _ascent_rate
    return _descent_rate


# Outer-wall long-wave radiation to the night-sky / Earth environment. The mission
# flies at night, so there is no absorbed solar flux; the effective radiative sink is
# taken at the stratospheric ambient minimum (US Standard Atmosphere 1976).
EXT_RADIATION = {
    'eps_ir': 0.90,      # EPP outer-shell long-wave emissivity
    'T_sink': 216.65,    # effective radiative-environment temperature [K] (-56.5 degC)
    'q_solar': 0.0,      # absorbed solar flux [W/m^2]
}


MISSION_CONFIG = {
    'R_box': R_box, 'L_box': L_box,
    'L_wall': L_wall, 'L_cap': L_cap,
    'R_int': R_int, 'L_int': L_int, 'D_int': D_int,
    'Nr': Nr, 'Nz': Nz, 'N_wall': N_wall,
    'dt': dt, 't_end': t_end, 'save_every': save_every,
    'h_inside': h_inside,
    'T_launch': T_launch,
    'h_alt_fn': h_alt_fn,
    'V_rel_fn': V_rel_fn,
    'ext_radiation': EXT_RADIATION,
}
