"""Non-component solids: passive PETG support shelves and optical windows.

Grid: planar (x, z), Nr=68, Nz=100, 2.5 mm cells, z=0 at the enclosure floor.
STRUCTURES are written into the mesh before components (mesh.build_maps), so a shelf
never overwrites an active device cell.
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

# Passive PETG structure: thin horizontal support shelves only (1-cell, 2 mm), each
# sitting below its supported components. 'petg' = solid member (k=0.20);
# 'petg_frame' = open frame (k=0.165).

STRUCTURES = [
    {'name': 'shelf_top',     'region': {'r_idx': (8, 60),  'z_idx': (69, 70)}, 'material': 'petg'},  # below upper payload bay
    {'name': 'shelf_mid',      'region': {'r_idx': (8, 60),  'z_idx': (53, 54)}, 'material': 'petg'},  # 2 mm shelf between the two middle decks
    {'name': 'platform_mid',   'region': {'r_idx': (8, 60),  'z_idx': (38, 39)}, 'material': 'petg'},  # 2 mm deck (underside now at ~95 mm after the 5-cell shift)
    {'name': 'shelf_battery', 'region': {'r_idx': (4, 64),  'z_idx': (6, 7)}, 'material': 'petg'},  # support below the wide battery
]
