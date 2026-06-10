"""Material property database (SI units: k [W/mK], rho [kg/m3], cp [J/kgK])."""

MATERIALS = {
    'air':         {'k': 0.025, 'rho': 1.2,    'cp': 1005.0, 'description': 'Internal air'},
    'eps':         {'k': 0.035, 'rho': 60.0,   'cp': 1700.0, 'description': 'EPP Thermobox wall (30 mm)'},
    'petg':        {'k': 0.20,  'rho': 1270.0, 'cp': 1400.0, 'description': 'PETG 3D-printed frame'},
    'petg_frame':  {'k': 0.165, 'rho': 1016.0, 'cp': 1400.0, 'description': 'Open PETG frame: 80% PETG + 20% air gap (parallel k)'},
    'battery':     {'k': 2.0,   'rho': 2500.0, 'cp': 1000.0, 'description': 'Li-ion battery pack'},
    'obc':         {'k': 1.0,   'rho': 1500.0, 'cp': 800.0,  'description': 'Jetson Orin Nano (PCB composite)'},
    'stm32':       {'k': 0.5,   'rho': 1500.0, 'cp': 800.0,  'description': 'Nucleo STM32 board'},
    'camera':      {'k': 0.5,   'rho': 1200.0, 'cp': 900.0,  'description': 'Camera module (EVK4 / GA100)'},
    'pcb_generic': {'k': 0.3,   'rho': 1500.0, 'cp': 800.0,  'description': 'Generic PCB / sensor module'},
    'nvme':        {'k': 5.0,   'rho': 2000.0, 'cp': 700.0,  'description': 'NVMe SSD'},
    'glass_optic': {'k': 1.0,   'rho': 2500.0, 'cp': 840.0,  'description': 'Optical glass (lens / window)'},
    'copper_wire': {'k': 50.0,  'rho': 4000.0, 'cp': 450.0,  'description': 'Wiring harness (effective)'},
}


def get_material(name: str) -> dict:
    if name not in MATERIALS:
        raise ValueError(f"Material '{name}' not in database. Available: {sorted(MATERIALS.keys())}")
    return MATERIALS[name]


def k_harmonic(k1: float, k2: float) -> float:
    if k1 + k2 == 0.0:
        return 0.0
    return 2.0 * k1 * k2 / (k1 + k2)
