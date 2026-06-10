"""
test_block_b.py – Unit tests for Block B (1-D implicit wall conduction solver).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.block_b import solve_wall, wall_inner_temperature, wall_outer_temperature

# EPS material properties
K, RHO, CP = 0.033, 15.0, 1500.0
# Geometry: 5-node wall, dx = 0.05/(5-1) = 0.0125 m
N, DX = 5, 0.0125
DT = 60.0   # s

def _solve(T_old, T_inf, h_ext, T_air, h_int=1.0):
    return solve_wall(T_old, T_inf, h_ext, T_air, h_int, K, RHO, CP, DX, DT)


# 1. Thermal equilibrium
def test_equilibrium_no_change():
    """Uniform IC matching BCs → solution unchanged."""
    T0 = np.full(N, 280.0)
    T_new = _solve(T0, T_inf=280.0, h_ext=10.0, T_air=280.0)
    assert np.allclose(T_new, 280.0, atol=1e-6), \
        "Thermal equilibrium must produce no temperature change"


# 2. Steady state monotone
def test_steady_state_monotone():
    """T_inf=220, T_air=300 → profile monotone increasing outer→inner."""
    T = np.full(N, 260.0)
    for _ in range(1000):
        T = _solve(T, T_inf=220.0, h_ext=10.0, T_air=300.0)
    # outer < inner
    assert T[0] < T[-1], "Outer surface must be colder than inner in this setup"
    # monotone
    diffs = np.diff(T)
    assert np.all(diffs > 0), "Profile must be monotone increasing outer→inner"


# 3. Energy conservation
def test_energy_conservation():
    """
    Over one timestep:
      Q_int (in from internal air) - Q_ext (out to atmosphere) ≈ ΔE_stored
    Tolerance: 1%
    """
    T_old = np.array([230.0, 240.0, 255.0, 270.0, 290.0])
    T_inf = 220.0; h_ext = 5.0; T_air = 300.0; h_int = 1.0

    T_new = solve_wall(T_old, T_inf, h_ext, T_air, h_int, K, RHO, CP, DX, DT)

    # Stored energy change: half-cell ends, full-cell interior
    dx_cells = np.array([DX/2] + [DX]*(N-2) + [DX/2])
    dE = np.sum(RHO * CP * dx_cells * (T_new - T_old))   # J/m2

    # Heat fluxes (W/m2) × dt
    Q_ext = h_ext * (T_new[0]  - T_inf) * DT   # heat leaving outer face
    Q_int = h_int * (T_air     - T_new[-1]) * DT  # heat entering inner face

    residual = abs((Q_int - Q_ext) - dE) / (abs(dE) + 1e-6)
    assert residual < 0.01, f"Energy balance error {residual*100:.2f}% > 1%"


# 4. Accessor functions
def test_accessors():
    T = np.array([210.0, 220.0, 240.0, 260.0, 280.0])
    assert wall_outer_temperature(T) == pytest.approx(210.0)
    assert wall_inner_temperature(T) == pytest.approx(280.0)


# 5. Minimum node validation
def test_single_node_raises():
    with pytest.raises(ValueError):
        _solve(np.array([280.0]), T_inf=220.0, h_ext=5.0, T_air=300.0)

def test_two_nodes_accepted():
    T = np.array([280.0, 280.0])
    T_new = solve_wall(T, 280.0, 5.0, 280.0, 1.0, K, RHO, CP, DX, DT)
    assert T_new.shape == (2,)


# 6. Large h_ext → outer node → T_inf
def test_large_h_ext_drives_outer_node():
    """With h_ext very large, outer node should rapidly reach T_inf."""
    T_inf = 200.0
    T = np.full(N, 290.0)
    T_new = solve_wall(T, T_inf, h_ext=10_000.0, T_air=290.0,
                       h_int=1.0, k_wall=K, rho_wall=RHO, cp_wall=CP,
                       dx=DX, dt=DT)
    assert abs(T_new[0] - T_inf) < 1.0, \
        "Outer node must snap to T_inf when h_ext is very large"


# 7. Implicit Euler stability
def test_unconditional_stability_large_dt():
    """Implicit Euler must not diverge even with very large timestep."""
    T = np.full(N, 290.0)
    T_new = solve_wall(T, 200.0, 10.0, 300.0, 1.0, K, RHO, CP, DX, dt=3600.0)
    assert np.all(np.isfinite(T_new)), "Large dt must not produce NaN/Inf"
    assert np.all(T_new >= 199.0) and np.all(T_new <= 301.0), \
        "Result must remain within physical bounds"
