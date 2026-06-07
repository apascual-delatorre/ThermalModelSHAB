"""
thermal_design.py - Non-component solids: PETG divider frame and optical windows.

Grid: Nr=32 (i 0-31), Nz=100 (j 0-99), 2.5 mm cells, z=0 at the enclosure floor.
"""

HEATERS = []
STRAPS = []

WINDOWS = [
    {
        'name':      'window_GA100',
        'area_m2':   0.015 * 0.015,
        'z_idx':     (72, 96),
        'thickness': 0.003,
        'material':  'glass_optic',
    },
    {
        'name':      'window_EVK4',
        'area_m2':   0.015 * 0.015,
        'z_idx':     (72, 96),
        'thickness': 0.003,
        'material':  'glass_optic',
    },
]

PETG_FRAME = [
    {'name': 'plate_L3_L2', 'region': {'r_idx': (0, 32), 'z_idx': (44, 46)}, 'material': 'petg'},
    {'name': 'plate_L2_L1', 'region': {'r_idx': (0, 32), 'z_idx': (70, 72)}, 'material': 'petg'},
    {'name': 'plate_top',   'region': {'r_idx': (0, 32), 'z_idx': (96, 100)}, 'material': 'petg'},
]
