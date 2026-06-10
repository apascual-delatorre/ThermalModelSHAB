"""
mesh.py - Planar (x, z) finite-volume mesh and material/source map assembly.

Cell centres at x=(i+0.5)dx, z=(j+0.5)dz, on a uniform Cartesian grid representing a
vertical longitudinal slice of the payload (x = left-right width, z = height), treated
as an extruded slab of out-of-plane depth D. The material map holds one material name
per cell; the source map holds the heat generation [W] per cell. Component, strap, and
(enabled) heater regions are written in that order, later entries overriding earlier.

(Names Nr/dr/r_idx are kept for call-site stability; they denote the planar x-direction.)
"""

import numpy as np
from .materials import get_material


def build_mesh(R_int: float, L_int: float, Nr: int, Nz: int):
    dr = R_int / Nr
    dz = L_int / Nz
    r = (np.arange(Nr) + 0.5) * dr
    z = (np.arange(Nz) + 0.5) * dz
    return r, z, dr, dz


def cell_geometry(Nr: int, Nz: int, dr: float, dz: float, D: float = 1.0):
    """Return uniform planar cell volume and face areas (V, A_x, A_z) for slab depth D.

    V = dx*dz*D ; A_x = dz*D (left/right faces) ; A_z = dx*D (top/bottom faces).
    """
    shape = (Nr, Nz)
    V = np.full(shape, dr * dz * D)
    A_x = np.full(shape, dz * D)
    A_z = np.full(shape, dr * D)
    return V, A_x, A_z


def build_maps(Nr: int, Nz: int, components: list, heaters: list, straps: list,
               structures: list | None = None):
    """Build the material_map (str per cell) and source_map (W per cell).

    Write order (later overrides earlier): structures -> components -> straps -> heaters.
    Passive PETG structures (shelves, partitions, the battery cage) are written FIRST so
    any powered component placed over them wins the overlap — structural PETG can never
    overwrite an active device; it is trimmed instead.
    """
    material_map = np.full((Nr, Nz), 'air', dtype=object)
    source_map = np.zeros((Nr, Nz), dtype=float)

    for s in (structures or []):
        ri0, ri1 = s['region']['r_idx']
        zi0, zi1 = s['region']['z_idx']
        material_map[ri0:ri1, zi0:zi1] = s.get('material', 'petg_frame')

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
