"""
mesh_viz.py -- Visual inspection of the compiled mesh maps.

Renders each cell coloured by its material (left panel) and by its heat
source [W] (right panel), so you can immediately verify that the config
assembled the mesh correctly before running a long simulation.

ORIENTATION (2026-06-06): plotted to match the CAD section drawing -- z is the
VERTICAL axis (floor z=0 at the bottom, top of cavity at the top) and the
axisymmetric (r,z) field is MIRRORED about the central axis so the full Ø160 mm
diameter is shown (r negative on the left, positive on the right), exactly like the
front-section CAD. Component labels are written once, on the right (+r) half.

Entry points
------------
    plot_mesh_maps(material_map, source_map, r, z, dr, dz,
                   components=None, heaters=None, straps=None,
                   save_path=None)

    inspect_config(cfg, save_path=None)   # convenience: builds maps then plots
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import MultipleLocator

# ── Material palette (ordered for consistent legend) ──────────────────────────
_PALETTE_ORDER = [
    'air', 'petg', 'aluminum', 'al_strap', 'heater',
    'battery', 'obc', 'stm32', 'camera',
    'pcb_generic', 'nvme', 'eps', 'glass_optic', 'copper_wire',
]
_PALETTE_HEX = {
    'air':         '#D6EAF8',   # pale blue
    'petg':        '#A9DFBF',   # pale green
    'aluminum':    '#AEB6BF',   # steel gray
    'al_strap':    '#AEB6BF',   # steel gray (foil strap)
    'heater':      '#E74C3C',   # red
    'battery':     '#E67E22',   # orange
    'obc':         '#6C3483',   # deep purple
    'stm32':       '#8E44AD',   # medium purple
    'camera':      '#F1C40F',   # yellow
    'pcb_generic': '#D4AC0D',   # amber
    'nvme':        '#17A589',   # teal
    'eps':         '#EAECEE',   # near-white
    'glass_optic': '#85C1E9',   # light blue glass
    'copper_wire': '#CA6F1E',   # copper
}
_FALLBACK_HEX = '#FADBD8'       # light pink for unknown materials


# ── Core plot function ─────────────────────────────────────────────────────────
def plot_mesh_maps(
    material_map: np.ndarray,
    source_map: np.ndarray,
    r: np.ndarray,
    z: np.ndarray,
    dr: float,
    dz: float,
    components: list | None = None,
    heaters: list | None = None,
    straps: list | None = None,
    save_path: str | None = None,
):
    """
    Two-panel figure showing the compiled mesh configuration in CAD orientation
    (z vertical, full mirrored diameter):

      Left  -- Material map: each cell coloured by material, with region
               outlines and labels for every component, heater, and strap.
      Right -- Source map: heat generation [W/cell] as a hot-colourmap heatmap.
    """
    Nr, Nz = material_map.shape

    # Cell-face coordinates in cm
    r_faces = np.linspace(0, Nr * dr, Nr + 1) * 1e2          # 0 … R   (Nr+1,)
    z_faces = np.linspace(0, Nz * dz, Nz + 1) * 1e2          # 0 … L   (Nz+1,)
    # Mirror r about the axis to show the full diameter -R … +R
    r_faces_full = np.concatenate([-r_faces[::-1], r_faces[1:]])   # (2Nr+1,)

    r_c = r * 1e2   # cell centres in cm
    z_c = z * 1e2

    # ── Build integer coding for material map ──────────────────────────────────
    unique_mats = list(_PALETTE_ORDER)
    for mat in np.unique(material_map):
        if mat not in unique_mats:
            unique_mats.append(str(mat))

    mat_to_idx = {mat: idx for idx, mat in enumerate(unique_mats)}
    hex_list   = [_PALETTE_HEX.get(mat, _FALLBACK_HEX) for mat in unique_mats]
    cmap_mat   = ListedColormap(hex_list)
    norm_mat   = BoundaryNorm(np.arange(-0.5, len(unique_mats)), cmap_mat.N)

    int_map = np.vectorize(lambda m: mat_to_idx[m])(material_map)  # (Nr, Nz)

    present_idx = sorted(set(int_map.flatten()))
    present_mats = [unique_mats[i] for i in present_idx]

    # ── Figure (portrait: z is now the tall vertical axis) ─────────────────────
    fig_w = max(11, Nr * 0.85 + 5)
    fig_h = max(7,  Nz * 0.22 + 2)
    fig = plt.figure(figsize=(fig_w, fig_h))
    fig.suptitle(
        f'Mesh Map Inspection  (CAD orientation: z vertical, full diameter)   '
        f'[{Nr}r x {Nz}z cells,  dr={dr*1e3:.1f} mm,  dz={dz*1e3:.1f} mm]',
        fontsize=11, fontweight='bold', y=0.99,
    )

    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=0.45,
                          left=0.07, right=0.86, top=0.93, bottom=0.07)
    ax_mat = fig.add_subplot(gs[0])
    ax_src = fig.add_subplot(gs[1])

    # ── Panel 1: Material map (mirrored, z vertical) ───────────────────────────
    int_full = _mirror(int_map)                       # (Nz, 2Nr)
    X, Y = np.meshgrid(r_faces_full, z_faces)         # (Nz+1, 2Nr+1)
    ax_mat.pcolormesh(
        X, Y, int_full,
        cmap=cmap_mat, norm=norm_mat,
        edgecolors='#777777', linewidth=0.3,
    )
    _style_ax(ax_mat, r_faces_full, z_faces, dr * 1e2, dz * 1e2, 'Material Map')

    patches = []
    for mat in _PALETTE_ORDER + [m for m in unique_mats if m not in _PALETTE_ORDER]:
        if mat in present_mats:
            patches.append(mpatches.Patch(
                facecolor=_PALETTE_HEX.get(mat, _FALLBACK_HEX),
                edgecolor='#555', linewidth=0.5, label=mat,
            ))
    ax_mat.legend(handles=patches, loc='upper left', bbox_to_anchor=(1.02, 1.0),
                  fontsize=8, title='Material', title_fontsize=8.5,
                  framealpha=0.95, edgecolor='#ccc')

    _annotate_regions(ax_mat, components or [], z_c, r_c, dz * 1e2, dr * 1e2,
                      use_label='label', text_color='white', border_color='white',
                      fontsize=5.5)
    enabled_heaters = [h for h in (heaters or []) if h.get('enabled', True)]
    _annotate_regions(ax_mat, enabled_heaters, z_c, r_c, dz * 1e2, dr * 1e2,
                      use_label='name', extra_line=lambda h: f"{h['power']} W",
                      text_color='white', border_color='#FFD700', fontsize=5.5,
                      border_lw=1.4)
    _annotate_regions(ax_mat, straps or [], z_c, r_c, dz * 1e2, dr * 1e2,
                      use_label='name', text_color='#111', border_color='#333',
                      fontsize=4.5, border_style=':')

    # ── Panel 2: Source map (mirrored, z vertical) ─────────────────────────────
    if source_map.max() > 0.0:
        src_full = _mirror(source_map)
        im = ax_src.pcolormesh(
            X, Y, src_full,
            cmap='hot_r', vmin=0, vmax=source_map.max(),
            edgecolors='#aaa', linewidth=0.2,
        )
        cb = fig.colorbar(im, ax=ax_src, pad=0.03, label='Heat source [W/cell]',
                          fraction=0.046)
        cb.ax.tick_params(labelsize=8)
        _annotate_regions(ax_src, enabled_heaters, z_c, r_c, dz * 1e2, dr * 1e2,
                          use_label='name', extra_line=lambda h: f"{h['power']} W",
                          text_color='white', border_color='white',
                          fontsize=6, border_lw=1.0)
    else:
        checker = (np.indices((Nr, Nz)).sum(axis=0) % 2) * 0.06
        ax_src.pcolormesh(X, Y, _mirror(checker),
                          cmap='Greys', vmin=0, vmax=1,
                          edgecolors='#bbb', linewidth=0.2)
        ax_src.text(0.5, 0.5, 'No active\nheat sources',
                    transform=ax_src.transAxes,
                    ha='center', va='center', fontsize=11, color='#777')
    _style_ax(ax_src, r_faces_full, z_faces, dr * 1e2, dz * 1e2, 'Source Map [W/cell]')

    if save_path:
        plt.savefig(save_path, dpi=160, bbox_inches='tight')
        print(f'[mesh_viz] Saved mesh map -> {save_path}')
    else:
        plt.show()
    plt.close(fig)


# ── Convenience wrapper ────────────────────────────────────────────────────────
def inspect_config(cfg: dict, save_path: str | None = None):
    """Build maps from a merged config dict and render them."""
    from .mesh import build_mesh, build_maps

    r, z, dr, dz = build_mesh(cfg['R_int'], cfg['L_int'], cfg['Nr'], cfg['Nz'])
    material_map, source_map = build_maps(
        cfg['Nr'], cfg['Nz'],
        cfg.get('components', []),
        cfg.get('heaters', []),
        cfg.get('straps', []),
    )
    plot_mesh_maps(
        material_map, source_map, r, z, dr, dz,
        components=cfg.get('components'),
        heaters=cfg.get('heaters'),
        straps=cfg.get('straps'),
        save_path=save_path,
    )


# ── Internal helpers ───────────────────────────────────────────────────────────
def _mirror(field_rz: np.ndarray) -> np.ndarray:
    """(Nr, Nz) field -> (Nz, 2Nr) mirrored about the axis for a full-diameter,
    z-vertical pcolormesh (rows = z increasing upward, cols = r from -R to +R)."""
    f_T = field_rz.T                                  # (Nz, Nr)  rows=z, cols=r
    return np.concatenate([f_T[:, ::-1], f_T], axis=1)  # (Nz, 2Nr)


def _style_ax(ax, r_faces_full, z_faces, dr_cm, dz_cm, title):
    ax.set_xlim(r_faces_full[0], r_faces_full[-1])
    ax.set_ylim(z_faces[0], z_faces[-1])              # z=0 (floor) at bottom
    ax.set_xlabel('r [cm]  (mirrored full diameter — axis at 0)', fontsize=9)
    ax.set_ylabel('z [cm]  (floor at bottom)', fontsize=9)
    ax.set_title(title, fontsize=10, pad=5)
    ax.set_aspect('equal')
    ax.tick_params(labelsize=8)
    ax.axvline(0.0, color='#555', lw=0.8, ls=(0, (4, 3)))   # central axis line
    ax.xaxis.set_minor_locator(MultipleLocator(dr_cm))
    ax.yaxis.set_minor_locator(MultipleLocator(dz_cm))
    ax.grid(which='minor', color='#ddd', linewidth=0.15)


def _region_centre_cm(region, z_c, r_c):
    ri0, ri1 = region['r_idx']
    zi0, zi1 = region['z_idx']
    ri1 = min(ri1, len(r_c)) - 1
    zi1 = min(zi1, len(z_c)) - 1
    r_mid = 0.5 * (r_c[ri0] + r_c[max(ri0, ri1)])
    z_mid = 0.5 * (z_c[zi0] + z_c[max(zi0, zi1)])
    return r_mid, z_mid


def _draw_border(ax, region, dz_cm, dr_cm, color, lw, ls):
    """Outline the region on BOTH mirrored halves (x=r, y=z)."""
    ri0, ri1 = region['r_idx']
    zi0, zi1 = region['z_idx']
    r_lo, r_hi = ri0 * dr_cm, ri1 * dr_cm
    z_lo, z_hi = zi0 * dz_cm, zi1 * dz_cm
    if r_hi <= r_lo or z_hi <= z_lo:
        return
    # right half (+r) and mirrored left half (-r)
    ax.add_patch(plt.Rectangle((r_lo, z_lo), r_hi - r_lo, z_hi - z_lo,
                 fill=False, edgecolor=color, linewidth=lw, linestyle=ls))
    ax.add_patch(plt.Rectangle((-r_hi, z_lo), r_hi - r_lo, z_hi - z_lo,
                 fill=False, edgecolor=color, linewidth=lw, linestyle=ls))


def _annotate_regions(ax, items, z_c, r_c, dz_cm, dr_cm,
                       use_label='label', extra_line=None,
                       text_color='white', border_color='white',
                       fontsize=5.5, border_lw=0.9, border_style='--'):
    for item in items:
        region = item.get('region')
        if region is None:
            continue
        ri0, ri1 = region['r_idx']
        zi0, zi1 = region['z_idx']
        if ri1 <= ri0 or zi1 <= zi0:
            continue

        _draw_border(ax, region, dz_cm, dr_cm, border_color, border_lw, border_style)

        r_mid, z_mid = _region_centre_cm(region, z_c, r_c)
        label = item.get(use_label, '')
        label = label.replace('_', '\n').replace(' ', '\n')
        if extra_line is not None:
            label = label + '\n' + extra_line(item)

        # Label once, on the right (+r) half — like the CAD callouts
        ax.text(r_mid, z_mid, label,
                ha='center', va='center',
                fontsize=fontsize, color=text_color,
                fontweight='bold', clip_on=True)
