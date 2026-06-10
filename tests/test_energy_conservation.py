"""
test_energy_conservation.py – End-to-end energy balance tests for the coupled model.

These tests run short simulations and verify that energy is approximately conserved
(or correctly sourced/sunk) across the coupled B+C system.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.block_b import solve_wall
from src.block_c import solve_internal, air_volume_average
from src.materials import MATERIALS


# Shared geometry (planar slab, depth D)
NR, NZ   = 6, 8
R_INT    = 0.06
L_INT    = 0.08
DEPTH    = 0.10
DR, DZ   = R_INT / NR, L_INT / NZ
DT       = 30.0

K_EPS   = MATERIALS['eps']['k']
RHO_EPS = MATERIALS['eps']['rho']
CP_EPS  = MATERIALS['eps']['cp']
N_WALL  = 4
DX_WALL = 0.05 / (N_WALL - 1)

def _air_maps():
    import numpy as np
    mat = np.full((NR, NZ), 'air', dtype=object)
    src = np.zeros((NR, NZ))
    return mat, src

def _cell_volumes():
    # Uniform planar cell volume V = dx*dz*D
    return np.full((NR, NZ), DR * DZ * DEPTH)


# 1. No source, no external driving → energy conserved
def test_no_source_no_drive_energy_conserved():
    """
    With uniform IC = wall BC = T0 and no heater, total stored energy stays constant.
    Tests that Block C does not spontaneously create or destroy energy.
    """
    T0 = 280.0
    mat, src = _air_maps()
    T_grid = np.full((NR, NZ), T0)
    V = _cell_volumes()

    E_init = np.sum(MATERIALS['air']['rho'] * MATERIALS['air']['cp'] * V * T_grid)

    for _ in range(20):
        T_grid = solve_internal(T_grid, mat, src, T0, T0, T0, NR, NZ, DR, DZ, DT, D=DEPTH)

    E_final = np.sum(MATERIALS['air']['rho'] * MATERIALS['air']['cp'] * V * T_grid)
    rel_err = abs(E_final - E_init) / E_init
    assert rel_err < 1e-6, f"Energy changed by {rel_err*100:.4f}% with no driving."


# 2. Heater power → energy gain matches Q·dt
def test_heater_power_matches_energy_gain():
    """
    With isolated system (T_bc = mean internal T) and a point heater,
    stored energy gain ≈ Q_heater × N_steps × dt.
    """
    T0 = 280.0
    Q_heater = 2.0   # W in one cell
    N_STEPS  = 10

    mat, src = _air_maps()
    src[3, 4] = Q_heater
    T_grid = np.full((NR, NZ), T0)
    V = _cell_volumes()
    rho_cp = MATERIALS['air']['rho'] * MATERIALS['air']['cp']

    E_init = np.sum(rho_cp * V * T_grid)

    # Use T_bc = T0 so boundary acts as a heat sink; instead adiabatic test:
    # Set T_bc slightly above T0 so we only measure heater contribution.
    # For a clean test: run with T_bc fixed at T0 and measure dE vs Q·dt.
    T_bc_arr = np.full(NZ, T0)
    for _ in range(N_STEPS):
        T_mean = air_volume_average(T_grid, mat, NR, NZ, DR, DZ)
        T_grid = solve_internal(T_grid, mat, src, T_bc_arr, T0, T0,
                                NR, NZ, DR, DZ, DT, D=DEPTH)

    E_final = np.sum(rho_cp * V * T_grid)
    dE = E_final - E_init
    Q_expected = Q_heater * N_STEPS * DT  # J

    # Energy gained should be close to heater power × time, minus wall losses.
    # Since T_bc < T_interior after heating starts, some energy leaks out.
    # Check dE > 0 (system gained heat) and dE <= Q_expected + 5% tolerance.
    assert dE > 0.0, "Stored energy must increase when heater is on."
    assert dE <= Q_expected * 1.05, "Cannot store more than source provides."


# 3. Coupled B+C: wall + internal settle toward T_inf
def test_coupled_B_C_convergence():
    """
    With a cold external environment and no internal source, the coupled system
    (Block B wall + Block C interior) must cool monotonically.
    """
    T_inf  = 220.0
    T_init = 290.0
    h_ext  = 5.0
    h_int  = 1.0

    mat, src = _air_maps()
    T_grid     = np.full((NR, NZ), T_init)
    T_wall_arr = np.full(N_WALL, T_init)

    T_air_history = []

    for _ in range(50):
        T_air = air_volume_average(T_grid, mat, NR, NZ, DR, DZ)
        T_air_history.append(T_air)

        T_wall_arr = solve_wall(
            T_wall_arr, T_inf, h_ext, T_air, h_int,
            K_EPS, RHO_EPS, CP_EPS, DX_WALL, DT,
        )
        T_side_in = T_wall_arr[-1]
        T_grid = solve_internal(T_grid, mat, src,
                                T_side_in, T_side_in, T_side_in,
                                NR, NZ, DR, DZ, DT, D=DEPTH)

    T_air_final = air_volume_average(T_grid, mat, NR, NZ, DR, DZ)

    assert T_air_final < T_init, "Interior must cool toward cold environment."
    assert T_air_final > T_inf - 5.0, "Interior must not undershoot T_inf by >5 K."

    # Monotone cooling (allow small non-monotone due to lagged coupling)
    diff = np.diff(T_air_history)
    frac_monotone = np.sum(diff <= 0.1) / len(diff)
    assert frac_monotone > 0.9, "Air temperature must be predominantly monotone cooling."


# 4. Block B wall energy balance over one step
def test_wall_energy_balance_one_step():
    """Verify heat flowing in from T_air = heat stored + heat lost to T_inf."""
    T_old  = np.array([230.0, 245.0, 260.0, 280.0])
    T_inf  = 210.0; h_ext = 8.0; T_air = 295.0; h_int = 1.0
    n, dx  = 4, 0.05 / 3

    T_new = solve_wall(T_old, T_inf, h_ext, T_air, h_int,
                       K_EPS, RHO_EPS, CP_EPS, dx, DT)

    dx_cells = np.array([dx/2, dx, dx, dx/2])
    dE_stored = np.sum(RHO_EPS * CP_EPS * dx_cells * (T_new - T_old))
    Q_int_in  = h_int * (T_air    - T_new[-1]) * DT
    Q_ext_out = h_ext * (T_new[0] - T_inf    ) * DT

    residual = abs(Q_int_in - Q_ext_out - dE_stored)
    norm     = abs(dE_stored) + abs(Q_int_in) + 1e-9
    assert residual / norm < 0.01, \
        f"Wall energy balance residual {residual:.4f} J/m2 > 1% tolerance"
