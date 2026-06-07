"""
Block A - External environment.

US Standard Atmosphere 1976 (piecewise to 47 km) and the Churchill-Bernstein
forced-convection correlation for a cylinder in cross-flow.
Inputs : altitude [m], relative velocity [m/s], box diameter and length [m].
Outputs: free-stream temperature T_inf [K] and external coefficient h_ext [W/m2K].
"""

import numpy as np

_g = 9.80665
_R = 287.058

_LAYERS = [
    (     0, 288.15, 101325.00, -0.0065),
    ( 11000, 216.65,  22632.10,  0.0000),
    ( 20000, 216.65,   5474.89, +0.0010),
    ( 32000, 228.65,    868.02, +0.0028),
    ( 47000, 270.65,    110.91,  0.0000),
]


def _atm_layer(h: float):
    layer = _LAYERS[0]
    for row in _LAYERS[1:]:
        if h >= row[0]:
            layer = row
        else:
            break
    return layer


def atmosphere(h: float) -> dict:
    """US Standard Atmosphere 1976. Returns T, P, rho, mu, k, cp, Pr."""
    h = float(np.clip(h, 0.0, 47000.0))
    h_base, T_base, P_base, lapse = _atm_layer(h)
    dh = h - h_base
    T = T_base + lapse * dh

    if abs(lapse) < 1e-10:
        P = P_base * np.exp(-_g * dh / (_R * T_base))
    else:
        P = P_base * (T / T_base) ** (-_g / (lapse * _R))

    rho = P / (_R * T)
    mu = 1.458e-6 * T**1.5 / (T + 110.4)
    k_air = 2.495e-3 * T**0.8646 / (1.0 + 245.4 * 10**(-12.0 / T) / T)
    cp_air = 1005.0
    Pr = mu * cp_air / k_air

    return {'T': T, 'P': P, 'rho': rho, 'mu': mu, 'k': k_air, 'cp': cp_air, 'Pr': Pr}


def _reynolds(rho: float, V: float, D: float, mu: float) -> float:
    return rho * V * D / mu


def _nusselt_cb(Re: float, Pr: float) -> float:
    """Churchill-Bernstein (1977) Nusselt number for a cylinder in cross-flow."""
    if Re * Pr < 0.2:
        return 0.3
    term1 = 0.62 * Re**0.5 * Pr**(1.0 / 3.0)
    term2 = (1.0 + (0.4 / Pr)**(2.0 / 3.0))**0.25
    term3 = (1.0 + (Re / 282_000.0)**(5.0 / 8.0))**(4.0 / 5.0)
    return 0.3 + (term1 / term2) * term3


def evaluate_block_a(h_alt: float, V_rel: float, D_box: float, L_box: float) -> tuple[float, float]:
    """Return free-stream temperature [K] and external convective coefficient [W/m2K]."""
    atm = atmosphere(h_alt)
    T_inf = atm['T']
    V_eff = max(float(V_rel), 1e-3)
    Re = _reynolds(atm['rho'], V_eff, D_box, atm['mu'])
    Nu = _nusselt_cb(Re, atm['Pr'])
    h_ext = Nu * atm['k'] / D_box
    return T_inf, h_ext
