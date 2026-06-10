"""
postprocessing.py - Visualisation and energy-balance diagnostics.

Functions
---------
plot_temperature_contour  : 2-D T field at a selected time index
plot_component_traces     : Component T vs time with limit bands
plot_environment          : T_inf and h_total vs time
plot_wall_temperatures    : Inner / outer wall temperature evolution
energy_balance_check      : Compute and print energy balance at each saved step
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# Colour helpers
_CMAP = 'RdBu_r'


# Contour plot
def plot_temperature_contour(
    results: dict,
    r: np.ndarray,
    z: np.ndarray,
    time_indices: list[int] | None = None,
    save_path: str | None = None,
):
    """
    Plot 2-D temperature contour at one or more saved time steps.

    Parameters
    ----------
    results      : output from coupling.run_simulation
    r, z         : cell-centre coordinate arrays [m]
    time_indices : list of indices into results['time'] to plot (default: last)
    save_path    : if given, save figure to this path instead of showing
    """
    T_all = results['T_grid']     # (n_saved, Nr, Nz)
    t_arr = results['time']

    if time_indices is None:
        time_indices = [len(t_arr) - 1]

    ncols = len(time_indices)
    # Portrait panels: z is the tall vertical axis (CAD orientation)
    fig, axes = plt.subplots(1, ncols, figsize=(3.2 * ncols, 6), squeeze=False)

    # Global colour range across all requested snapshots for consistency
    T_min = min(T_all[k].min() for k in time_indices) - 273.15
    T_max = max(T_all[k].max() for k in time_indices) - 273.15

    # Planar (x, z) section: x = left-right width (left wall at 0), z vertical. No mirror.
    X, Z = np.meshgrid(r * 1e2, z * 1e2)                  # (Nz, Nr) cm

    for ax, k in zip(axes[0], time_indices):
        T_C = (T_all[k] - 273.15).T                       # (Nz, Nr)
        cf = ax.contourf(X, Z, T_C, levels=20, cmap=_CMAP, vmin=T_min, vmax=T_max)
        ax.set_xlabel('x [cm]  (left wall at 0)')
        ax.set_ylabel('z [cm]  (floor at bottom)')
        ax.set_aspect('equal')
        ax.set_title(f't = {t_arr[k]/60:.1f} min')
        fig.colorbar(cf, ax=ax, label='T [degC]')

    fig.suptitle('Internal Temperature Field (planar section: x horizontal, z vertical)',
                 fontsize=13)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[postprocessing] Saved contour plot -> {save_path}")
    else:
        plt.show()
    plt.close(fig)


# Component temperature traces
def plot_component_traces(
    results: dict,
    components_cfg: list,
    save_path: str | None = None,
):
    """
    Plot component mean temperatures vs time with operational limit bands.

    Parameters
    ----------
    results        : output from coupling.run_simulation
    components_cfg : list of component dicts from components_config
    save_path      : optional file path to save figure
    """
    t_min = results['time'] / 60.0   # s -> min
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = plt.cm.tab10(np.linspace(0, 1, len(components_cfg)))

    for comp, color in zip(components_cfg, colors):
        lbl = comp['label']
        T_trace = results['T_components'].get(lbl)
        if T_trace is None:
            continue
        ax.plot(t_min, np.array(T_trace) - 273.15, label=lbl, color=color, lw=1.5)

        # Operational limits (if defined and not TBD)
        T_op_min = comp.get('T_op_min')
        T_op_max = comp.get('T_op_max')
        if T_op_min is not None:
            ax.axhline(T_op_min - 273.15, color=color, ls='--', lw=0.7, alpha=0.6)
        if T_op_max is not None:
            ax.axhline(T_op_max - 273.15, color=color, ls='--', lw=0.7, alpha=0.6)

    ax.set_xlabel('Time [min]')
    ax.set_ylabel('Temperature [degC]')
    ax.set_title('Component Temperatures vs Time')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[postprocessing] Saved component traces -> {save_path}")
    else:
        plt.show()
    plt.close(fig)


# Environment overview
def plot_environment(
    results: dict,
    h_alt_fn,
    save_path: str | None = None,
):
    """Plot T_inf, h_total, and altitude vs time."""
    t_min = results['time'] / 60.0
    T_inf_C  = results['T_inf_arr']  - 273.15
    h_arr    = results['h_total_arr']
    h_km     = np.array([h_alt_fn(t) / 1000.0 for t in results['time']])

    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)

    axes[0].plot(t_min, h_km, 'b')
    axes[0].set_ylabel('Altitude [km]')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t_min, T_inf_C, 'r')
    axes[1].set_ylabel('T_inf [degC]')
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(t_min, h_arr, 'g')
    axes[2].set_ylabel('h_total [W/m2K]')
    axes[2].set_xlabel('Time [min]')
    axes[2].grid(True, alpha=0.3)

    fig.suptitle('External Environment vs Time')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[postprocessing] Saved environment plot -> {save_path}")
    else:
        plt.show()
    plt.close(fig)


# Wall temperature history
def plot_wall_temperatures(
    results: dict,
    save_path: str | None = None,
):
    """Plot inner and outer surface temperatures for side, top, bottom walls."""
    t_min = results['time'] / 60.0
    fig, ax = plt.subplots(figsize=(9, 4))

    for key, label, color in [
        ('T_wall_side', 'Side wall', 'steelblue'),
        ('T_wall_top',  'Top cap',   'coral'),
        ('T_wall_bot',  'Bottom cap','seagreen'),
    ]:
        w = results[key]  # (n_saved, N_wall)
        T_out = w[:, 0]  - 273.15
        T_in  = w[:, -1] - 273.15
        ax.plot(t_min, T_in,  color=color, lw=1.8, label=f'{label} inner')
        ax.plot(t_min, T_out, color=color, lw=0.9, ls='--', label=f'{label} outer')

    ax.set_xlabel('Time [min]')
    ax.set_ylabel('Temperature [degC]')
    ax.set_title('Wall Surface Temperatures')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[postprocessing] Saved wall temperature plot -> {save_path}")
    else:
        plt.show()
    plt.close(fig)


# Energy balance check
def energy_balance_check(results: dict, cfg: dict, verbose: bool = True) -> dict:
    """
    Compute a simplified energy balance at each saved timestep.

    Checks:
      Q_stored  = Σ rho*cp*V*ΔT/dt  over all internal cells
      Q_source  = total heater power (constant for now)
      Q_wall    = approximate heat flux through wall inner surface
                  ~ h_inside * A_wall_inner * (T_air - T_wall_inner)

    Returns dict with arrays for each quantity.
    """
    from .materials import MATERIALS

    Nr   = cfg['Nr']
    Nz   = cfg['Nz']
    dr   = cfg['R_int'] / Nr
    dz   = cfg['L_int'] / Nz
    D    = cfg.get('D_int', 2.0 * cfg['R_int'])
    dt   = cfg['dt']

    # Planar cell volumes (uniform slab of depth D)
    V_2d = np.full((Nr, Nz), dr * dz * D)

    # Heater total power
    Q_source_total = sum(
        h['power'] for h in cfg.get('heaters', []) if h.get('enabled', True)
    )

    T_grids  = results['T_grid']     # (n_saved, Nr, Nz)
    T_airs   = results['T_air']
    T_walls  = results['T_wall_side']  # (n_saved, N_wall)
    h_inside = cfg.get('h_inside', 1.0)

    R_int   = cfg['R_int']
    L_int   = cfg['L_int']
    W       = Nr * dr   # interior width (planar)
    A_side  = 2.0 * (W * L_int) + 2.0 * (L_int * D)   # lateral inner-wall area (planar box)
    A_caps  = 2.0 * (W * D)                            # top + bottom cap area

    Q_stored_arr = []
    Q_wall_arr   = []

    for k in range(1, len(T_grids)):
        dT_dt = (T_grids[k] - T_grids[k - 1]) / dt
        # Volume-averaged rho*cp (simplified: assume air everywhere)
        rho_cp = MATERIALS['air']['rho'] * MATERIALS['air']['cp']
        Q_stored = float(np.sum(rho_cp * V_2d * dT_dt))

        T_air   = T_airs[k]
        T_wi    = T_walls[k, -1]
        Q_wall  = h_inside * A_side * (T_air - T_wi)

        Q_stored_arr.append(Q_stored)
        Q_wall_arr.append(Q_wall)

    result = {
        'Q_stored':      np.array(Q_stored_arr),
        'Q_source':      Q_source_total,
        'Q_wall_approx': np.array(Q_wall_arr),
    }

    if verbose:
        print("\n[Energy Balance - time-averaged]")
        print(f"  Mean Q_stored  : {np.mean(result['Q_stored']):.2f} W")
        print(f"  Q_source total : {result['Q_source']:.2f} W")
        print(f"  Mean Q_wall_~  : {np.mean(result['Q_wall_approx']):.2f} W")

    return result
