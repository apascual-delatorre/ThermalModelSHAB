"""
test_block_c.py – Unit tests for Block C (2-D planar internal solver).

Tests:
  1. Thermal equilibrium  : uniform IC = uniform BCs → field stays uniform
  2. Centre-vs-wall gradient: a heated centre stays warmer than the cold side walls
  3. Dirichlet BC enforcement: cells near a wall → T_r_wall after long run
  4. Source term          : cell temperatures increase when heater power is on
  5. Left wall (i=0)      : no artefact — i=0 is now a Dirichlet wall, not an axis
  6. air_volume_average   : returns correct average over air cells
  7. component_temperature: returns mean of the specified region
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.block_c import solve_internal, air_volume_average, component_temperature
from src.mesh    import build_mesh, build_maps

# Common small mesh
NR, NZ = 5, 6
R_INT  = 0.05   # m
L_INT  = 0.06   # m
DR     = R_INT / NR
DZ     = L_INT / NZ
DT     = 60.0   # s

def _air_maps(nr=NR, nz=NZ):
    mat = np.full((nr, nz), 'air', dtype=object)
    src = np.zeros((nr, nz))
    return mat, src


# 1. Thermal equilibrium
def test_equilibrium():
    T0   = 280.0
    mat, src = _air_maps()
    T_old = np.full((NR, NZ), T0)
    T_new = solve_internal(T_old, mat, src, T0, T0, T0, NR, NZ, DR, DZ, DT)
    assert np.allclose(T_new, T0, atol=1e-6), \
        "Uniform BC + uniform IC should produce a uniform field."


# 2. Centre-vs-wall gradient
def test_centre_warmer_than_walls():
    """With cold walls on both sides and a heated centre column, the centre cells
    must settle warmer than the wall-adjacent cells (no symmetry axis any more)."""
    T_wall = 220.0   # cold walls (both lateral + caps)
    mat, src = _air_maps()
    src[NR // 2, :] = 2.0   # heat the central x-column

    T_old = np.full((NR, NZ), T_wall)
    for _ in range(500):
        T_old = solve_internal(T_old, mat, src, T_wall, T_wall, T_wall,
                               NR, NZ, DR, DZ, DT)

    T_centre = T_old[NR // 2, NZ // 2]
    T_left   = T_old[0, NZ // 2]
    T_right  = T_old[NR - 1, NZ // 2]
    assert T_centre > T_left + 1.0 and T_centre > T_right + 1.0, \
        "Heated centre must be warmer than both cold side walls."


# 3. Dirichlet BC at outer wall
def test_dirichlet_outer_wall():
    T_wall = 200.0
    mat, src = _air_maps()
    T_old = np.full((NR, NZ), 290.0)

    for _ in range(1000):
        T_old = solve_internal(T_old, mat, src, T_wall, T_wall, T_wall,
                               NR, NZ, DR, DZ, DT)

    # In steady state with no internal source, all cells → T_wall
    assert np.allclose(T_old, T_wall, atol=0.5), \
        "With uniform BC and no source, all cells must converge to T_wall."


# 4. Source term raises temperature
def test_source_raises_temperature():
    T_bc = 250.0
    mat, src = _air_maps()
    src[2, 3] = 5.0   # 5 W heater at one cell

    T_no_src = np.full((NR, NZ), T_bc)
    T_src    = np.full((NR, NZ), T_bc)

    # Run both with and without source for 200 steps
    mat0, src0 = _air_maps()
    for _ in range(200):
        T_no_src = solve_internal(T_no_src, mat0, src0, T_bc, T_bc, T_bc,
                                  NR, NZ, DR, DZ, DT)
        T_src    = solve_internal(T_src,    mat,  src,  T_bc, T_bc, T_bc,
                                  NR, NZ, DR, DZ, DT)

    assert T_src[2, 3] > T_no_src[2, 3] + 1.0, \
        "Heated cell must be warmer than equivalent cell without source."
    assert np.all(T_src >= T_no_src - 0.01), \
        "Source should only raise (or maintain) temperatures everywhere."


# 5. Left wall (i=0): no artefact
def test_left_wall_no_artefact():
    """The left-wall cells (i=0, now Dirichlet) should not produce NaN/unphysical values."""
    T_bc = 250.0
    mat, src = _air_maps()
    T_old = np.full((NR, NZ), 290.0)
    src[0, :] = 1.0   # put source directly on the left-wall cells

    for _ in range(50):
        T_old = solve_internal(T_old, mat, src, T_bc, T_bc, T_bc,
                               NR, NZ, DR, DZ, DT)

    assert not np.any(np.isnan(T_old)), "NaN in solution – axis singularity?"
    assert not np.any(np.isinf(T_old)), "Inf in solution."
    assert np.all(T_old >= T_bc - 1.0), "Temperature below BC – unphysical."


# 6. air_volume_average
def test_air_volume_average_uniform():
    T_field = np.full((NR, NZ), 280.0)
    mat, _  = _air_maps()
    T_avg   = air_volume_average(T_field, mat, NR, NZ, DR, DZ)
    assert abs(T_avg - 280.0) < 1e-6, "Uniform field → average must equal T."


def test_air_volume_average_weighted():
    """One hot x-column out of NR is diluted by the rest (uniform planar cell volume)."""
    mat, _ = _air_maps()
    T_field = np.full((NR, NZ), 250.0)
    T_field[0, :] = 350.0    # one column hot; 1 of NR columns

    T_avg = air_volume_average(T_field, mat, NR, NZ, DR, DZ)
    # Plain mean: (1*350 + (NR-1)*250) / NR  → well below 280 for NR=5
    assert T_avg < 280.0, "A single hot column should be diluted by the rest."


# 7. component_temperature
def test_component_temperature():
    T_field = np.full((NR, NZ), 270.0)
    T_field[1:3, 2:4] = 300.0   # patch of 2×2 cells at 300 K

    region = {'r_idx': (1, 3), 'z_idx': (2, 4)}
    T_c = component_temperature(T_field, region)
    assert abs(T_c - 300.0) < 1e-6, "component_temperature must return patch mean."


def test_component_temperature_empty_region():
    T_field = np.full((NR, NZ), 270.0)
    region  = {'r_idx': (3, 3), 'z_idx': (3, 3)}   # empty slice
    T_c = component_temperature(T_field, region)
    assert np.isnan(T_c), "Empty region should return NaN."
