"""
components_config.py - Payload component list: layout, thermal loads, and limits.

Each entry maps a component to a rectangular (r, z) cell region on the axisymmetric
mesh (Nr=32, Nz=100; 2.5 mm cells; i = mm-from-axis / 2.5; j = mm-from-floor / 2.5),
its material, mass, steady electrical dissipation, and operating/storage limits [K].

Layout reproduces the CAD section (report Fig. CAD) as four stacked rows:
  ROW 1 top    (j 72-96): EVK4 + lens, Strato Tracker, GA100
  ROW 2 mid-up (j 56-70): STM32, SPOT Trace, IMU, MS8607
  ROW 3 mid-low(j 46-56): GNSS / SD cluster, Flex 5 powerbank
  ROW 4 bottom (j 0-44) : Jetson Orin Nano (inner) + Battery (outer) + storage
Components are inset to leave a 5 mm air clearance to the side wall.
"""


def _C(c):
    return c + 273.15


COMPONENTS = [
    {
        'label': 'NVIDIA Jetson Orin Nano', 'subsystem': 'OBC', 'material': 'obc',
        'region': {'r_idx': (0, 16), 'z_idx': (6, 34)},
        'mass': 0.260, 'power': 7.0,
        'T_op_min': _C(-25), 'T_op_max': _C(90), 'T_stor_min': _C(-40), 'T_stor_max': _C(90),
        'source': 'NVIDIA DS-10653-001 Rev.1.0',
    },
    {
        'label': 'Battery (Li-ion / Li-Po)', 'subsystem': 'EPS', 'material': 'battery',
        'region': {'r_idx': (16, 30), 'z_idx': (10, 34)},
        'mass': 1.0, 'power': 0.3,
        'T_op_min': _C(-20), 'T_op_max': _C(60), 'T_stor_min': _C(-40), 'T_stor_max': _C(60),
        'source': 'IEC 62133 generic Li-ion/Li-Po',
    },
    {
        'label': '250 GB SSD (NVMe M.2)', 'subsystem': 'OBC', 'material': 'nvme',
        'region': {'r_idx': (0, 14), 'z_idx': (34, 42)},
        'mass': 0.010, 'power': 3.0,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-55), 'T_stor_max': _C(95),
        'source': 'JEDEC JESD218 NVMe M.2',
    },
    {
        'label': 'USB Stick (USB 3.0)', 'subsystem': 'OBC', 'material': 'pcb_generic',
        'region': {'r_idx': (14, 22), 'z_idx': (34, 42)},
        'mass': 0.005, 'power': 3.0,
        'T_op_min': _C(-25), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'USB 3.0 device',
    },
    {
        'label': 'STM32 Nucleo F446RE', 'subsystem': 'OBC', 'material': 'stm32',
        'region': {'r_idx': (6, 18), 'z_idx': (56, 68)},
        'mass': 0.050, 'power': 0.3,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-65), 'T_stor_max': _C(150),
        'source': 'ST UM1724 Rev.14',
    },
    {
        'label': 'GNSS Module (u-blox NEO-M9N)', 'subsystem': 'Sensors', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 14), 'z_idx': (46, 54)},
        'mass': 0.010, 'power': 0.15,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-55), 'T_stor_max': _C(85),
        'source': 'u-blox UBX-19014285 Rev.05',
    },
    {
        'label': 'SD Card Reader + Card', 'subsystem': 'OBC', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 14), 'z_idx': (54, 56)},
        'mass': 0.005, 'power': 0.05,
        'T_op_min': _C(-25), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'Generic SD card spec',
    },
    {
        'label': 'IMU (TDK ICM-20948) x2', 'subsystem': 'Sensors', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 6), 'z_idx': (62, 70)},
        'mass': 0.005, 'power': 0.01,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'TDK InvenSense ICM-20948 Rev.1.3',
    },
    {
        'label': 'Env. Sensor MS8607 (T/P/H) x2', 'subsystem': 'Sensors', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 6), 'z_idx': (56, 62)},
        'mass': 0.002, 'power': 0.005,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'TE Connectivity MS8607 Rev.A',
    },
    {
        'label': 'SPOT Trace', 'subsystem': 'Recovery', 'material': 'pcb_generic',
        'region': {'r_idx': (18, 30), 'z_idx': (58, 68)},
        'mass': 0.070, 'power': 0.3,
        'T_op_min': _C(-40), 'T_op_max': _C(60), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'SPOT Trace product spec',
    },
    {
        'label': 'Strato Tracker', 'subsystem': 'Recovery', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 10), 'z_idx': (74, 88)},
        'mass': 0.060, 'power': 0.5,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'Stratotracker product spec',
    },
    {
        'label': 'Flex 5 Powerbank', 'subsystem': 'EPS', 'material': 'battery',
        'region': {'r_idx': (14, 30), 'z_idx': (46, 56)},
        'mass': 0.400, 'power': 0.4,
        'T_op_min': _C(-10), 'T_op_max': _C(45), 'T_stor_min': _C(-20), 'T_stor_max': _C(60),
        'source': 'Generic Li-ion powerbank spec',
    },
    {
        'label': 'Wolfgang GA100 (frame camera)', 'subsystem': 'Payload', 'material': 'camera',
        'region': {'r_idx': (22, 30), 'z_idx': (76, 96)},
        'mass': 0.120, 'power': 3.0,
        'T_op_min': _C(-10), 'T_op_max': _C(40), 'T_stor_min': _C(-20), 'T_stor_max': _C(45),
        'source': 'Action-camera equivalent (GoPro Hero 12/13 class)',
    },
    {
        'label': 'Prophesee EVK4 (IMX636)', 'subsystem': 'Payload', 'material': 'camera',
        'region': {'r_idx': (10, 22), 'z_idx': (74, 90)},
        'mass': 0.130, 'power': 1.5,
        'T_op_min': _C(-20), 'T_op_max': _C(60), 'T_stor_min': _C(-30), 'T_stor_max': _C(70),
        'source': 'Prophesee Metavision EVK4 HD Rev.C (IMX636)',
    },
    {
        'label': 'Soyo 1/2.5" f2.0 C-Mount Lens', 'subsystem': 'Payload', 'material': 'glass_optic',
        'region': {'r_idx': (14, 20), 'z_idx': (90, 96)},
        'mass': 0.050, 'power': 0.0,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'Passive optical element',
    },
    {
        'label': 'GNSS Antenna (ceramic patch)', 'subsystem': 'Sensors', 'material': 'pcb_generic',
        'region': {'r_idx': (0, 10), 'z_idx': (90, 96)},
        'mass': 0.020, 'power': 0.0,
        'T_op_min': _C(-40), 'T_op_max': _C(85), 'T_stor_min': _C(-40), 'T_stor_max': _C(85),
        'source': 'Passive ceramic patch antenna',
    },
    {
        'label': 'Wiring & Connectors', 'subsystem': 'EPS', 'material': 'copper_wire',
        'region': {'r_idx': (28, 30), 'z_idx': (6, 76)},
        'mass': 0.200, 'power': 0.5,
        'T_op_min': _C(-55), 'T_op_max': _C(125), 'T_stor_min': _C(-55), 'T_stor_max': _C(125),
        'source': 'Copper harness per IPC-2221',
    },
]
