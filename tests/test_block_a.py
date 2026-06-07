"""
test_block_a.py – Unit tests for Block A (US Standard Atmosphere + Churchill-Bernstein).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.block_a import atmosphere, evaluate_block_a


# ── Atmosphere correctness ─────────────────────────────────────────────────────

def test_sea_level_temperature():
    atm = atmosphere(0.0)
    assert abs(atm['T'] - 288.15) < 0.01, "Sea-level T must be 288.15 K"

def test_sea_level_pressure():
    atm = atmosphere(0.0)
    assert abs(atm['P'] - 101325.0) < 1.0, "Sea-level P must be 101325 Pa"

def test_tropopause_temperature():
    atm = atmosphere(11000.0)
    assert abs(atm['T'] - 216.65) < 0.5, "Tropopause T must be ≈216.65 K"

def test_stratosphere_temperature():
    atm = atmosphere(35000.0)
    # Layer boundary: 32 km=228.65 K, lapse +2.8 K/km → T(35km)=237.05 K
    assert 234.0 <= atm['T'] <= 242.0, "35 km T must be in stratosphere range"

def test_ideal_gas_law_across_altitudes():
    R = 287.058
    for h in [0, 5000, 11000, 20000, 35000]:
        atm = atmosphere(h)
        rho_from_gas = atm['P'] / (R * atm['T'])
        assert abs(rho_from_gas - atm['rho']) / atm['rho'] < 0.001, \
            f"Ideal gas violated at h={h} m"

def test_density_decreases_with_altitude():
    rhos = [atmosphere(h)['rho'] for h in [0, 10000, 20000, 35000]]
    assert all(rhos[i] > rhos[i+1] for i in range(len(rhos)-1)), \
        "Density must decrease monotonically with altitude"

def test_temperature_monotone_troposphere():
    Ts = [atmosphere(h)['T'] for h in range(0, 11000, 1000)]
    assert all(Ts[i] > Ts[i+1] for i in range(len(Ts)-1)), \
        "Temperature must decrease monotonically in troposphere"

def test_altitude_clamped_to_47km():
    # Should not raise; returns stratopause values
    atm_high = atmosphere(100_000.0)
    atm_cap  = atmosphere(47_000.0)
    assert abs(atm_high['T'] - atm_cap['T']) < 0.01

def test_no_nan_across_full_range():
    for h in np.linspace(0, 47000, 200):
        atm = atmosphere(h)
        for key in ['T', 'P', 'rho', 'mu', 'k', 'cp', 'Pr']:
            assert np.isfinite(atm[key]), f"NaN/Inf in atm['{key}'] at h={h} m"


# ── evaluate_block_a ───────────────────────────────────────────────────────────

def test_block_a_sea_level_nominal():
    T_inf, h_total = evaluate_block_a(h_alt=0.0, V_rel=5.0, D_box=0.3, L_box=0.3)
    assert abs(T_inf - 288.15) < 0.1, "T_inf must match sea-level standard"
    assert h_total > 0.0, "h_total must be positive"

def test_block_a_float_phase_low_h():
    """V_rel=0 uses 1e-3 floor → h should be very small but > 0."""
    _, h_float  = evaluate_block_a(35000.0, 0.0,  0.3, 0.3)
    _, h_ascent = evaluate_block_a(35000.0, 5.0,  0.3, 0.3)
    assert h_float > 0.0
    assert h_ascent > h_float, "Ascending gondola must have higher h than floating one"

def test_block_a_stratosphere_T_inf():
    T_inf, _ = evaluate_block_a(35000.0, 5.0, 0.3, 0.3)
    assert abs(T_inf - atmosphere(35000.0)['T']) < 1e-6, \
        "T_inf must exactly match atmosphere() output"

def test_block_a_h_increases_with_velocity():
    hs = [evaluate_block_a(10000.0, v, 0.3, 0.3)[1] for v in [1.0, 5.0, 10.0]]
    assert hs[0] < hs[1] < hs[2], "h_total must increase monotonically with V_rel"

def test_block_a_h_decreases_at_high_altitude():
    """Thin air at float altitude → much lower h than at ascent altitudes."""
    _, h_low  = evaluate_block_a(1000.0,  5.0, 0.3, 0.3)
    _, h_high = evaluate_block_a(35000.0, 5.0, 0.3, 0.3)
    assert h_high < h_low, "h_total must decrease as air thins with altitude"
