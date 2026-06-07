"""
coupling.py - Lagged time-stepping loop.

Per step: evaluate Block A (T_inf, h_ext); take the lagged air temperature; advance
the side/top/bottom walls and the window pane with Block B; advance the internal field
with Block C using the new inner-wall temperatures.
"""

import numpy as np
import time as _time

from .block_a import evaluate_block_a
from .block_b import solve_wall
from .block_c import solve_internal, air_volume_average, component_temperature
from .mesh import build_mesh, build_maps
from .materials import MATERIALS


def run_simulation(cfg: dict) -> dict:
    """Run the coupled simulation and return time-series results."""
    R_int = cfg['R_int']
    L_int = cfg['L_int']
    Nr = cfg['Nr']
    Nz = cfg['Nz']

    R_box = cfg['R_box']
    L_box = cfg['L_box']
    D_box = 2.0 * R_box

    L_wall = cfg['L_wall']
    N_wall = cfg['N_wall']
    dx_wall = L_wall / (N_wall - 1)

    k_eps = MATERIALS['eps']['k']
    rho_eps = MATERIALS['eps']['rho']
    cp_eps = MATERIALS['eps']['cp']

    windows = cfg.get('windows', [])
    window_area_z = np.zeros(Nz)
    win_pane = None
    if windows:
        wmat = MATERIALS[windows[0].get('material', 'glass_optic')]
        tot_area = sum(w['area_m2'] for w in windows)
        win_thick = sum(w['area_m2'] * w.get('thickness', 0.003) for w in windows) / tot_area
        win_pane = {'k': wmat['k'], 'rho': wmat['rho'], 'cp': wmat['cp'],
                    'dx': win_thick / (N_wall - 1)}
        for w in windows:
            z0, z1 = w['z_idx']
            n = max(z1 - z0, 1)
            window_area_z[z0:z1] += w['area_m2'] / n

    dt = cfg['dt']
    t_end = cfg['t_end']
    save_every = cfg.get('save_every', 1)
    n_steps = int(np.ceil(t_end / dt))

    h_alt_fn = cfg['h_alt_fn']
    V_rel_fn = cfg['V_rel_fn']
    h_inside_base = cfg.get('h_inside', 1.0)
    h_inside_fn_cfg = cfg.get('h_inside_fn', None)

    r, z, dr, dz = build_mesh(R_int, L_int, Nr, Nz)
    material_map, source_map = build_maps(
        Nr, Nz, cfg.get('components', []), cfg.get('heaters', []), cfg.get('straps', []))

    # Components with a power_fn(t, h_alt) override static power each step
    dynamic_comps = []
    for comp in cfg.get('components', []):
        if 'power_fn' not in comp:
            continue
        ri0, ri1 = comp['region']['r_idx']
        zi0, zi1 = comp['region']['z_idx']
        n_cells = (ri1 - ri0) * (zi1 - zi0)
        if n_cells > 0:
            source_map[ri0:ri1, zi0:zi1] -= comp.get('power', 0.0) / n_cells
            dynamic_comps.append({
                'r_idx': (ri0, ri1), 'z_idx': (zi0, zi1),
                'n_cells': n_cells, 'power_fn': comp['power_fn'],
            })

    T0 = cfg['T_launch']
    T_grid = np.full((Nr, Nz), T0)
    T_wall_side = np.full(N_wall, T0)
    T_wall_top = np.full(N_wall, T0)
    T_wall_bot = np.full(N_wall, T0)
    T_wall_win = np.full(N_wall, T0)

    comp_labels = [c['label'] for c in cfg.get('components', [])]
    results = {
        'time': [], 'T_grid': [], 'T_air': [],
        'T_wall_side': [], 'T_wall_top': [], 'T_wall_bot': [],
        'T_inf_arr': [], 'h_total_arr': [], 'h_inside_arr': [],
        'T_components': {lbl: [] for lbl in comp_labels},
    }

    t_cpu_start = _time.perf_counter()
    print(f"[coupling] Starting simulation: {n_steps} steps, dt={dt}s, grid {Nr}x{Nz}")

    for step in range(n_steps + 1):
        t = step * dt

        h_alt = h_alt_fn(t)
        V_rel = V_rel_fn(t)
        T_inf, h_total = evaluate_block_a(h_alt, V_rel, D_box, L_box)

        h_inside = h_inside_fn_cfg(h_alt) if h_inside_fn_cfg is not None else h_inside_base

        T_air = air_volume_average(T_grid, material_map, Nr, Nz, dr, dz)

        T_wall_side = solve_wall(T_wall_side, T_inf, h_total, T_air, h_inside,
                                 k_eps, rho_eps, cp_eps, dx_wall, dt)
        T_wall_top = solve_wall(T_wall_top, T_inf, h_total, T_air, h_inside,
                                k_eps, rho_eps, cp_eps, dx_wall, dt)
        T_wall_bot = solve_wall(T_wall_bot, T_inf, h_total, T_air, h_inside,
                                k_eps, rho_eps, cp_eps, dx_wall, dt)

        T_side_inner = T_wall_side[-1]
        T_top_inner = T_wall_top[-1]
        T_bot_inner = T_wall_bot[-1]

        T_window_inner = None
        if win_pane is not None:
            T_wall_win = solve_wall(T_wall_win, T_inf, h_total, T_air, h_inside,
                                    win_pane['k'], win_pane['rho'], win_pane['cp'],
                                    win_pane['dx'], dt)
            T_window_inner = T_wall_win[-1]

        if dynamic_comps:
            current_source = source_map.copy()
            for dc in dynamic_comps:
                ri0, ri1 = dc['r_idx']
                zi0, zi1 = dc['z_idx']
                p = dc['power_fn'](t, h_alt)
                current_source[ri0:ri1, zi0:zi1] += p / dc['n_cells']
        else:
            current_source = source_map

        if step > 0:
            T_grid = solve_internal(T_grid, material_map, current_source,
                                    T_side_inner, T_top_inner, T_bot_inner,
                                    Nr, Nz, dr, dz, dt,
                                    window_area=window_area_z, T_window=T_window_inner)

        if step % save_every == 0:
            results['time'].append(t)
            results['T_grid'].append(T_grid.copy())
            results['T_air'].append(T_air)
            results['T_wall_side'].append(T_wall_side.copy())
            results['T_wall_top'].append(T_wall_top.copy())
            results['T_wall_bot'].append(T_wall_bot.copy())
            results['T_inf_arr'].append(T_inf)
            results['h_total_arr'].append(h_total)
            results['h_inside_arr'].append(h_inside)
            for comp in cfg.get('components', []):
                results['T_components'][comp['label']].append(
                    component_temperature(T_grid, comp['region']))
            if step % (10 * save_every) == 0:
                elapsed = _time.perf_counter() - t_cpu_start
                print(f"  t={t/60:.1f} min  h={h_alt/1000:.1f} km  "
                      f"T_inf={T_inf-273.15:.1f}C  T_air={T_air-273.15:.1f}C  "
                      f"h_ext={h_total:.3f} W/m2K  [{elapsed:.0f}s CPU]")

    results['time'] = np.array(results['time'])
    results['T_grid'] = np.array(results['T_grid'])
    results['T_air'] = np.array(results['T_air'])
    results['T_wall_side'] = np.array(results['T_wall_side'])
    results['T_wall_top'] = np.array(results['T_wall_top'])
    results['T_wall_bot'] = np.array(results['T_wall_bot'])
    results['T_inf_arr'] = np.array(results['T_inf_arr'])
    results['h_total_arr'] = np.array(results['h_total_arr'])
    results['h_inside_arr'] = np.array(results['h_inside_arr'])
    for lbl in results['T_components']:
        results['T_components'][lbl] = np.array(results['T_components'][lbl])

    print(f"[coupling] Done. Total CPU time: {_time.perf_counter() - t_cpu_start:.1f}s")
    return results
