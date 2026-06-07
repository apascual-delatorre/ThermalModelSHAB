"""main.py - Entry point: run the two OBC operating scenarios and write the
figures used by each flight-readiness report.

Two scenarios are evaluated over the ascent-to-apogee window:
  report_launch : OBC powered from launch until one hour after 16 km
  report_16km   : OBC powered only from 16 km, for one hour

Each scenario writes its temperature-contour and component-temperature figures into
the corresponding report folder; the shared mesh map and environment plot are written
into both. All other settings (geometry, mesh, materials, mission profile) are common.
"""

import sys
import os
import copy
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from config.mission_config import MISSION_CONFIG
from config.components_config import COMPONENTS
from config.thermal_design import HEATERS, STRAPS, WINDOWS

from src.coupling import run_simulation
from src.mesh import build_mesh
from src.mesh_viz import inspect_config
from src.block_a import atmosphere
from src.postprocessing import (
    plot_temperature_contour,
    plot_component_traces,
    plot_environment,
)


ALT_IMAGING = 16_000.0       # altitude at which imaging begins [m]
P0 = 101_325.0               # sea-level reference pressure [Pa]
T_LAUNCH = 5.0 + 273.15      # initial cage temperature (cold-night launch) [K]
P_OBC = 7.0                  # Jetson Orin Nano dissipation [W]


def h_inside(h_alt: float, h0: float = 1.5) -> float:
    """Internal natural-convection coefficient as a function of altitude.

    Laminar enclosure convection gives Nu ~ Ra^(1/4) with Ra ~ rho^2 ~ P^2, so the
    coefficient scales with the square root of ambient pressure:
        h_inside(h) = h0 * sqrt(P(h) / P0).
    """
    return h0 * float(np.sqrt(atmosphere(h_alt)['P'] / P0))


def build_cfg() -> dict:
    """Assemble the common analysis configuration."""
    cfg = dict(MISSION_CONFIG)
    cfg['components'] = COMPONENTS
    cfg['heaters'] = HEATERS
    cfg['straps'] = STRAPS
    cfg['windows'] = WINDOWS
    cfg['T_launch'] = T_LAUNCH
    cfg['h_inside_fn'] = h_inside
    return cfg


def with_jetson_schedule(cfg: dict, power_fn) -> dict:
    """Return a copy of cfg whose Jetson dissipation follows power_fn(t, h_alt)."""
    cfg2 = dict(cfg)
    cfg2['components'] = copy.deepcopy(cfg['components'])
    for comp in cfg2['components']:
        if comp['label'] == 'NVIDIA Jetson Orin Nano':
            comp['power_fn'] = power_fn
            break
    return cfg2


def contour_indices(times, t_start=None, n=5):
    """Pick n snapshot indices spread evenly over the time axis.

    If t_start is given, the snapshots are spread over [t_start, t_end] instead of
    the full window. This is used to focus the temperature-contour figure on the
    interval the reader cares about (for example, from the OBC power-on altitude
    through to power-off).
    """
    t0 = times[0] if t_start is None else float(t_start)
    targets = np.linspace(t0, times[-1], n)
    return sorted({int(np.argmin(np.abs(times - tt))) for tt in targets})


def print_summary(results: dict, components: list, label: str) -> None:
    """Print min/max temperatures and cold-side margin for each component."""
    print(f"\n-- Component Temperature Summary  [{label}] --")
    print(f"{'Component':<35} {'T_min [degC]':>10}  {'T_max [degC]':>10}  "
          f"{'T_op_min [degC]':>13}  Status")
    print("-" * 85)
    for comp in components:
        T_trace = results['T_components'].get(comp['label'])
        if T_trace is None or len(T_trace) == 0:
            continue
        T_min_C = float(np.min(T_trace)) - 273.15
        T_max_C = float(np.max(T_trace)) - 273.15
        T_lim_C = comp['T_op_min'] - 273.15
        status = 'OK' if T_min_C >= T_lim_C else 'FAIL COLD'
        print(f"  {comp['label']:<33} {T_min_C:>10.1f}  {T_max_C:>10.1f}  "
              f"{T_lim_C:>13.1f}  {status}")


def main():
    print("=" * 60)
    print("  LHAB Thermal Model")
    print("=" * 60)

    base_cfg = build_cfg()
    print(f"\nGrid           : {base_cfg['Nr']}r x {base_cfg['Nz']}z  "
          f"(dr={base_cfg['R_int']/base_cfg['Nr']*1e3:.1f} mm, "
          f"dz={base_cfg['L_int']/base_cfg['Nz']*1e3:.1f} mm)")
    print(f"Duration       : {base_cfg['t_end']/60:.1f} min  "
          f"(dt={base_cfg['dt']}s, save every {base_cfg['save_every']} steps)")
    print(f"Initial T      : {base_cfg['T_launch'] - 273.15:.1f} degC")

    # Imaging starts on reaching 16 km; the imaging window is one hour.
    t_16 = next((t for t in range(0, int(base_cfg['t_end']) + 1, int(base_cfg['dt']))
                 if base_cfg['h_alt_fn'](t) >= ALT_IMAGING), 3200)
    t_off = t_16 + 3600.0
    print(f"16 km at t={t_16/60:.1f} min; imaging ends at t={t_off/60:.1f} min")

    def power_launch(t, h):
        return P_OBC if t <= t_off else 0.0

    def power_16km(t, h):
        return P_OBC if t_16 <= t <= t_off else 0.0

    # Each scenario also sets the contour window: the launch case spans the whole
    # flight, while the 16 km case is sampled from power-on (16 km) to power-off so
    # the heating evolution during the active window is visible.
    scenarios = [
        ('report_launch', 'OBC from launch', power_launch, None),
        ('report_16km',   'OBC from 16 km',  power_16km,   t_16),
    ]

    r, z, _, _ = build_mesh(base_cfg['R_int'], base_cfg['L_int'],
                            base_cfg['Nr'], base_cfg['Nz'])

    report_dirs = []
    first_results = None
    for folder, label, power_fn, contour_start in scenarios:
        out_dir = os.path.join(_HERE, folder)
        os.makedirs(out_dir, exist_ok=True)
        report_dirs.append(out_dir)

        def out(name, d=out_dir):
            return os.path.join(d, name)

        cfg = with_jetson_schedule(base_cfg, power_fn)
        print(f"\n=== {label} ===")
        results = run_simulation(cfg)
        if first_results is None:
            first_results = results

        snap_idx = contour_indices(results['time'], t_start=contour_start)
        plot_temperature_contour(results, r, z, time_indices=snap_idx,
                                 save_path=out('temperature_contour.png'))
        plot_component_traces(results, cfg['components'],
                              save_path=out('component_temperatures.png'))
        print_summary(results, cfg['components'], label)

    # Shared figures: mesh layout and external environment (identical for both scenarios).
    for d in report_dirs:
        inspect_config(base_cfg, save_path=os.path.join(d, 'mesh_map.png'))
        plot_environment(first_results, base_cfg['h_alt_fn'],
                         save_path=os.path.join(d, 'environment.png'))

    print("\nDone. Figures written to report_launch/ and report_16km/")


if __name__ == '__main__':
    main()
