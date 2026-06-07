"""
Block C - 2-D axisymmetric internal field.

Finite-volume formulation on a uniform (r, z) grid, implicit Euler, solved with a
sparse direct solver. Cell (i,j) centre at r=(i+0.5)dr, z=(j+0.5)dz; flat index i*Nz+j.
Boundary conditions: Dirichlet inner-wall temperature on the outer ring and on the
top/bottom caps (from Block B); zero flux on the axis. Interface conductances use the
harmonic-mean conductivity. Optional glass windows add a parallel conductance on the
outer ring at the camera-level cells.
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from .materials import MATERIALS, k_harmonic


def solve_internal(T_old, material_map, source_map, T_r_wall, T_top, T_bot,
                   Nr, Nz, dr, dz, dt, window_area=None, T_window=None):
    """Advance the 2-D internal temperature field one timestep."""
    if np.isscalar(T_r_wall):
        T_r_wall = np.full(Nz, float(T_r_wall))
    T_r_wall = np.asarray(T_r_wall, dtype=float)

    if window_area is None:
        window_area = np.zeros(Nz)
    window_area = np.asarray(window_area, dtype=float)

    N = Nr * Nz
    rows, cols, vals = [], [], []
    b = np.zeros(N)

    k_map = np.vectorize(lambda m: MATERIALS[m]['k'])(material_map)
    rho_map = np.vectorize(lambda m: MATERIALS[m]['rho'])(material_map)
    cp_map = np.vectorize(lambda m: MATERIALS[m]['cp'])(material_map)

    def idx(i, j):
        return i * Nz + j

    def _add(row, col, val):
        rows.append(row); cols.append(col); vals.append(val)

    for i in range(Nr):
        r_inner = i * dr
        r_outer = (i + 1) * dr
        A_ri = 2.0 * np.pi * r_inner * dz
        A_ro = 2.0 * np.pi * r_outer * dz
        A_z = np.pi * (r_outer**2 - r_inner**2)
        V = A_z * dz

        for j in range(Nz):
            ij = idx(i, j)
            k = k_map[i, j]
            rho = rho_map[i, j]
            cp = cp_map[i, j]

            thermal_mass = rho * cp * V / dt
            diag = thermal_mass
            rhs = thermal_mass * T_old[i, j] + source_map[i, j]

            if i == 0:
                pass
            else:
                G = k_harmonic(k, k_map[i - 1, j]) * A_ri / dr
                diag += G
                _add(ij, idx(i - 1, j), -G)

            if i < Nr - 1:
                G = k_harmonic(k, k_map[i + 1, j]) * A_ro / dr
                diag += G
                _add(ij, idx(i + 1, j), -G)
            else:
                A_win = min(window_area[j], A_ro) if T_window is not None else 0.0
                A_eps = A_ro - A_win
                G_eps = k * A_eps / (dr / 2.0)
                diag += G_eps
                rhs += G_eps * T_r_wall[j]
                if A_win > 0.0:
                    G_win = k * A_win / (dr / 2.0)
                    diag += G_win
                    rhs += G_win * T_window

            if j > 0:
                G = k_harmonic(k, k_map[i, j - 1]) * A_z / dz
                diag += G
                _add(ij, idx(i, j - 1), -G)
            else:
                G = k * A_z / (dz / 2.0)
                diag += G
                rhs += G * T_bot

            if j < Nz - 1:
                G = k_harmonic(k, k_map[i, j + 1]) * A_z / dz
                diag += G
                _add(ij, idx(i, j + 1), -G)
            else:
                G = k * A_z / (dz / 2.0)
                diag += G
                rhs += G * T_top

            _add(ij, ij, diag)
            b[ij] = rhs

    A_mat = coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsr()
    return spsolve(A_mat, b).reshape(Nr, Nz)


def air_volume_average(T_grid, material_map, Nr, Nz, dr, dz):
    """Volume-weighted mean temperature of the air cells (falls back to global mean)."""
    i_idx = np.arange(Nr)
    A_z = np.pi * ((i_idx + 1)**2 - i_idx**2) * dr**2
    V_2d = np.outer(A_z * dz, np.ones(Nz))
    air_mask = (material_map == 'air')
    total_vol = np.sum(V_2d[air_mask])
    if total_vol == 0.0:
        return float(np.mean(T_grid))
    return float(np.sum(T_grid[air_mask] * V_2d[air_mask]) / total_vol)


def component_temperature(T_grid, region):
    """Spatial mean temperature over a component cell region."""
    ri0, ri1 = region['r_idx']
    zi0, zi1 = region['z_idx']
    patch = T_grid[ri0:ri1, zi0:zi1]
    if patch.size == 0:
        return float('nan')
    return float(np.mean(patch))
