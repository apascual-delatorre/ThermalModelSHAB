"""
Block B - 1-D transient wall conduction.

Implicit Euler through N nodes across the wall thickness, solved as a tridiagonal
system. Node 0 is the outer surface (Robin BC with the atmosphere); node N-1 is the
inner surface (Robin BC with the internal air). Boundary nodes use half control
volumes, interior nodes full control volumes.
"""

import numpy as np
from scipy.linalg import solve_banded

SIGMA_SB = 5.670374419e-8   # Stefan-Boltzmann constant [W/m^2 K^4]


def solve_wall(T_old, T_inf, h_ext, T_air, h_int, k_wall, rho_wall, cp_wall, dx, dt,
               eps_ir=0.0, T_sink=0.0, q_solar=0.0):
    """Advance the wall temperature array one timestep (implicit Euler).

    Optional external radiation on the outer surface (node 0):
      eps_ir  : long-wave surface emissivity (0 disables radiation).
      T_sink  : effective radiative-environment temperature [K] (space + Earth IR).
      q_solar : absorbed solar flux [W/m^2] = alpha_solar * incident flux.
    Radiation is linearized about the previous outer-surface temperature.
    """
    N = len(T_old)
    if N < 2:
        raise ValueError("Wall must have at least 2 nodes.")

    alpha = k_wall / dx
    cap_half = rho_wall * cp_wall * (dx / 2.0) / dt
    cap_full = rho_wall * cp_wall * dx / dt

    ab = np.zeros((3, N))
    b = np.zeros(N)

    ab[1, 0] = cap_half + h_ext + alpha
    ab[0, 1] = -alpha
    b[0] = cap_half * T_old[0] + h_ext * T_inf
    if eps_ir > 0.0:
        h_rad = eps_ir * SIGMA_SB * 4.0 * T_old[0]**3   # linearized about previous T
        ab[1, 0] += h_rad
        b[0] += h_rad * T_sink + q_solar

    for i in range(1, N - 1):
        ab[2, i - 1] = -alpha
        ab[1, i] = cap_full + 2.0 * alpha
        ab[0, i + 1] = -alpha
        b[i] = cap_full * T_old[i]

    ab[2, N - 2] = -alpha
    ab[1, N - 1] = cap_half + h_int + alpha
    b[N - 1] = cap_half * T_old[N - 1] + h_int * T_air

    return solve_banded((1, 1), ab, b)


def wall_inner_temperature(T_wall: np.ndarray) -> float:
    return float(T_wall[-1])


def wall_outer_temperature(T_wall: np.ndarray) -> float:
    return float(T_wall[0])
