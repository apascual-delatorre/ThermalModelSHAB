"""Payload component list: layout, thermal loads, and limits.

Each entry maps a component to a rectangular cell region on the planar (x, z) mesh
(Nr=68, Nz=100, 2.5 mm cells; i = x-cell from the left wall, j = floor-relative
height). Fields: material, mass [kg], steady electrical dissipation [W], and
operating/storage temperature limits [K]. Component x-positions follow the dimensioned
CAD section, preserving the left-right asymmetry of the layout. The lower bay is a
stacked topology: the battery sits on a thin horizontal PETG shelf with the Jetson
board above it across an open air gap. PETG members are horizontal shelves only
(see thermal_design.py STRUCTURES), written into the mesh before components.
"""


def _C(c):
    return c + 273.15


# Components flagged 'obc_gated' draw power only while the OBC (Jetson) is running;
# main.py applies the per-scenario schedule. Unflagged components keep their static
# `power` for the whole mission.

COMPONENTS = [
    # Lower bay: battery below in an open PETG cage, Jetson board above with ~80%
    # x-overlap across an open air gap (no solid PETG plate between them).
    {
        'label': 'Battery (Li-ion / Li-Po)', 'subsystem': 'EPS', 'material': 'battery',
        'region': {'r_idx': (4, 64), 'z_idx': (7, 20)},  # wide bottom block, 10 mm air each side (x 10-160 mm)
        'mass': 1.0, 'power': 0.3,
        'T_op_min': _C(-20), 'T_op_max': _C(60), 'T_stor_min': _C(-40), 'T_stor_max': _C(60),
        'source': 'IEC 62133 generic Li-ion/Li-Po',
    },
    {
        # Jetson carrier/body sitting ABOVE the battery cage (~80 % x-overlap with the
        # battery below). Passive body; the SoC/heatsink subregion carries the load.
        'label': 'NVIDIA Jetson Orin Nano (board)', 'subsystem': 'OBC', 'material': 'obc',
        'region': {'r_idx': (20, 48), 'z_idx': (22, 30)},  # centered on the cavity (cell 34 / x85 mm), over the wide battery
        'mass': 0.180, 'power': 0.0,
        'T_op_min': _C(-25), 'T_op_max': _C(90), 'T_stor_min': _C(-40), 'T_stor_max': _C(90),
        'source': 'NVIDIA DS-10653-001 Rev.1.0',
    },
    {
        # Active hot block / heatsink — right-biased, carries the full Jetson load.
        'label': 'NVIDIA Jetson Orin Nano (SoC)', 'subsystem': 'OBC', 'material': 'obc',
        'region': {'r_idx': (34, 46), 'z_idx': (26, 30)},  # right-of-centre inside the centered board
        'mass': 0.080, 'power': 7.0, 'obc_gated': True,
        'T_op_min': _C(-25), 'T_op_max': _C(90), 'T_stor_min': _C(-40), 'T_stor_max': _C(90),
        'source': 'NVIDIA DS-10653-001 Rev.1.0',
    },
    {
        'label': 'STM32 Nucleo F446RE', 'subsystem': 'OBC', 'material': 'stm32',
        'region': {'r_idx': (8, 32), 'z_idx': (54, 59)},  # CAD: upper-mid deck, left; 13.5 mm tall -> 5 cells (12.5 mm at 2.5 mm grid)
        'mass': 0.050, 'power': 0.3,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-65), 'T_stor_max': _C(150),
        'source': 'ST UM1724 Rev.14',
    },
    {
        'label': 'SPOT Trace (upper deck)', 'subsystem': 'Recovery', 'material': 'pcb_generic',
        'region': {'r_idx': (40, 60), 'z_idx': (54, 64)},  # CAD: upper-mid deck, right (beside STM32)
        'mass': 0.070, 'power': 0.3,
        'T_op_min': _C(-40), 'T_op_max': _C(60), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'SPOT Trace product spec',
    },
    {
        'label': 'SPOT Trace (lower deck)', 'subsystem': 'Recovery', 'material': 'pcb_generic',
        'region': {'r_idx': (8, 32), 'z_idx': (41, 53)},  # CAD: lower-mid deck, left, 30 mm tall (2nd unit; props assumed = upper)
        'mass': 0.070, 'power': 0.3,
        'T_op_min': _C(-40), 'T_op_max': _C(60), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'SPOT Trace product spec (2nd unit assumed identical)',
    },
    {
        'label': 'Strato Tracker', 'subsystem': 'Recovery', 'material': 'pcb_generic',
        'region': {'r_idx': (29, 45), 'z_idx': (70, 82)},  # CAD: centre, 5 mm right of EVK4, 30 mm tall (12 cells)
        'mass': 0.060, 'power': 0.5,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'Stratotracker product spec',
    },
    {
        'label': 'Flex 5 Powerbank', 'subsystem': 'EPS', 'material': 'battery',
        'region': {'r_idx': (40, 60), 'z_idx': (41, 52)},  # CAD: lower-mid deck, right, 28 mm tall (shorter than SPOT)
        'mass': 0.400, 'power': 0.4,
        'T_op_min': _C(-10), 'T_op_max': _C(45), 'T_stor_min': _C(-20), 'T_stor_max': _C(60),
        'source': 'Generic Li-ion powerbank spec',
    },
    {
        'label': 'Wolfgang GA100 (frame camera)', 'subsystem': 'Payload', 'material': 'camera',
        'region': {'r_idx': (46, 57), 'z_idx': (70, 94)},  # CAD: right (28 mm wide, 59 mm tall)
        'mass': 0.120, 'power': 3.0,
        'T_op_min': _C(-10), 'T_op_max': _C(40), 'T_stor_min': _C(-20), 'T_stor_max': _C(45),
        'source': 'Action-camera equivalent (GoPro Hero 12/13 class)',
    },
    {
        'label': 'Prophesee EVK4 (IMX636)', 'subsystem': 'Payload', 'material': 'camera',
        'region': {'r_idx': (11, 27), 'z_idx': (70, 92)},  # CAD: left, 28 mm from wall, 40 mm wide, 56 mm tall (~22 cells)
        'mass': 0.130, 'power': 1.5, 'obc_gated': True,
        'T_op_min': _C(-20), 'T_op_max': _C(60), 'T_stor_min': _C(-30), 'T_stor_max': _C(70),
        'source': 'Prophesee Metavision EVK4 HD Rev.C (IMX636)',
    },
]
