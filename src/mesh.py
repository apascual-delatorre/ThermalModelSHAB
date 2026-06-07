"""
mesh.py - Axisymmetric (r, z) finite-volume mesh and material/source map assembly.

Cell centres at r=(i+0.5)dr, z=(j+0.5)dz. The material map holds one material name
per cell; the source map holds the heat generation [W] per cell. Component, strap, and
(enabled) heater regions are written in that order, later entries overriding earlier.
"""

import numpy as np
from .materials import get_material


def build_mesh(R_int: float, L_int: float, Nr: int, Nz: int):
    dr = R_int / Nr
    dz = L_int / Nz
    r = (np.arange(Nr) + 0.5) * dr
    z = (np.arange(Nz) + 0.5) * dz
    return r, z, dr, dz


def cell_geometry(Nr: int, Nz: int, dr: float, dz: float):
    """Return cell volumes and face areas (V, A_r_inner, A_r_outer, A_z)."""
    i = np.arange(Nr)
    r_inner = i * dr
    r_outer = (i + 1) * dr

    A_r_inner_1d = 2 * np.pi * r_inner * dz
    A_r_outer_1d = 2 * np.pi * r_outer * dz
    A_z_1d = np.pi * (r_outer**2 - r_inner**2)
    V_1d = A_z_1d * dz

    ones = np.ones(Nz)
    V = np.outer(V_1d, ones)
    A_r_inner = np.outer(A_r_inner_1d, ones)
    A_r_outer = np.outer(A_r_outer_1d, ones)
    A_z = np.outer(A_z_1d, ones)
    return V, A_r_inner, A_r_outer, A_z


def build_maps(Nr: int, Nz: int, components: list, heaters: list, straps: list):
    """Build the material_map (str per cell) and source_map (W per cell)."""
    material_map = np.full((Nr, Nz), 'air', dtype=object)
    source_map = np.zeros((Nr, Nz), dtype=float)

    for comp in components:
        ri0, ri1 = comp['region']['r_idx']
        zi0, zi1 = comp['region']['z_idx']
        material_map[ri0:ri1, zi0:zi1] = comp.get('material', 'pcb_generic')
        p = comp.get('power', 0.0)
        if p > 0.0:
            n_cells = (ri1 - ri0) * (zi1 - zi0)
            if n_cells > 0:
                source_map[ri0:ri1, zi0:zi1] += p / n_cells

    for strap in straps:
        ri0, ri1 = strap['region']['r_idx']
        zi0, zi1 = strap['region']['z_idx']
        material_map[ri0:ri1, zi0:zi1] = strap.get('material', 'aluminum')

    for htr in heaters:
        if not htr.get('enabled', True):
            continue
        ri0, ri1 = htr['region']['r_idx']
        zi0, zi1 = htr['region']['z_idx']
        material_map[ri0:ri1, zi0:zi1] = 'heater'
        n_cells = (ri1 - ri0) * (zi1 - zi0)
        if n_cells > 0:
            source_map[ri0:ri1, zi0:zi1] += htr['power'] / n_cells

    return material_map, source_map
