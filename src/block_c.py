"""
Block C - 2-D planar internal field (vertical longitudinal section).

Finite-volume formulation on a uniform Cartesian (x, z) grid, implicit Euler, solved
with a sparse direct solver. (x, z) is a vertical slice through the payload: x is the
left-right width (cell 0 at the left wall), z is height (cell 0 at the floor). The slice
is treated as an extruded slab of out-of-plane depth D, so every cell has the same
volume V = dx*dz*D and face areas A_x = dz*D (left/right), A_z = dx*D (top/bottom).

Boundary conditions: Dirichlet inner-wall temperature on both lateral walls (i=0 and
i=Nr-1, both fed the side-wall temperature from Block B) and on the top/bottom caps.
Interface conductances use the harmonic-mean conductivity. Optional glass windows add a
parallel conductance on the right wall at the camera-level cells. The index names
Nr/dr/r_idx denote the planar x-direction.
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from .materials import MATERIALS, k_harmonic


def solve_internal(T_old, material_map, source_map, T_r_wall, T_top, T_bot,
                   Nr, Nz, dr, dz, dt, D=1.0, window_area=None, T_window=None):
    """Advance the 2-D planar internal temperature field one timestep.

    T_r_wall feeds both lateral walls (the enclosure side wall). D is the out-of-plane
    slab depth [m]; with a uniform grid every cell shares the same metrics.
    """
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

    # Uniform planar cell metrics (extruded slab of depth D).
    A_x = dz * D        # left/right (x) faces
    A_z = dr * D        # top/bottom (z) faces
    V = dr * dz * D     # cell volume

    def idx(i, j):
        return i * Nz + j

    def _add(row, col, val):
        rows.append(row); cols.append(col); vals.append(val)

    for i in range(Nr):
        for j in range(Nz):
            ij = idx(i, j)
            k = k_map[i, j]
            rho = rho_map[i, j]
            cp = cp_map[i, j]

            thermal_mass = rho * cp * V / dt
            diag = thermal_mass
            rhs = thermal_mass * T_old[i, j] + source_map[i, j]

            # left face (x-)
            if i == 0:
                # left side wall (Dirichlet)
                G = k * A_x / (dr / 2.0)
                diag += G
                rhs += G * T_r_wall[j]
            else:
                G = k_harmonic(k, k_map[i - 1, j]) * A_x / dr
                diag += G
                _add(ij, idx(i - 1, j), -G)

            # right face (x+)
            if i < Nr - 1:
                G = k_harmonic(k, k_map[i + 1, j]) * A_x / dr
                diag += G
                _add(ij, idx(i + 1, j), -G)
            else:
                # right side wall (Dirichlet), optional window in parallel
                A_win = min(window_area[j], A_x) if T_window is not None else 0.0
                A_eps = A_x - A_win
                G_eps = k * A_eps / (dr / 2.0)
                diag += G_eps
                rhs += G_eps * T_r_wall[j]
                if A_win > 0.0:
                    G_win = k * A_win / (dr / 2.0)
                    diag += G_win
                    rhs += G_win * T_window

            # bottom face (z-)
            if j > 0:
                G = k_harmonic(k, k_map[i, j - 1]) * A_z / dz
                diag += G
                _add(ij, idx(i, j - 1), -G)
            else:
                G = k * A_z / (dz / 2.0)
                diag += G
                rhs += G * T_bot

            # top face (z+)
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
    """Mean temperature of the air cells.

    On the uniform planar grid every cell has the same volume, so the volume-weighted
    average reduces to a plain arithmetic mean over the air cells (falls back to the
    global mean when there are none).
    """
    air_mask = (material_map == 'air')
    if not air_mask.any():
        return float(np.mean(T_grid))
    return float(np.mean(T_grid[air_mask]))


def component_temperature(T_grid, region):
    """Spatial mean temperature over a component cell region."""
    ri0, ri1 = region['r_idx']
    zi0, zi1 = region['z_idx']
    patch = T_grid[ri0:ri1, zi0:zi1]
    if patch.size == 0:
        return float('nan')
    return float(np.mean(patch))
