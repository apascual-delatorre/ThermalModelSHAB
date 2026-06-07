"""
Block B - 1-D transient wall conduction.

Implicit Euler through N nodes across the wall thickness, solved as a tridiagonal
system. Node 0 is the outer surface (Robin BC with the atmosphere); node N-1 is the
inner surface (Robin BC with the internal air). Boundary nodes use half control
volumes, interior nodes full control volumes.
"""

import numpy as np
from scipy.linalg import solve_banded


def solve_wall(T_old, T_inf, h_ext, T_air, h_int, k_wall, rho_wall, cp_wall, dx, dt):
    """Advance the wall temperature array one timestep (implicit Euler)."""
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
