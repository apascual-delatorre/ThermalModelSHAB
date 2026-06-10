# LHAB Thermal Model

## Purpose

A design tool for high-altitude balloon (LHAB) payload thermal management. It is a
preliminary model suitable for design iteration and trade studies.

## Overview

The model couples three thermal blocks, advanced with a lagged coupling each timestep:

- **Block A**: US Standard Atmosphere 1976 + Churchill-Bernstein cross-flow convection
  (external environment).
- **Block B**: 1D implicit wall conduction for the side wall, end caps, and optical
  windows. The outer surface exchanges convection and long-wave radiation with the
  environment; the internal convective coefficient is altitude dependent,
  `h_inside(h) = h0 * sqrt(P(h)/P0)`.
- **Block C**: 2D planar (x, z) finite-volume sparse solver for the internal field. Both
  lateral walls are independent Dirichlet boundaries, so the left-right asymmetric
  component layout is resolved directly without a symmetry assumption.

The mission flies at night, so the radiative boundary is a heat-loss path only (no
absorbed solar flux). Radiative inputs are documented in `ASSUMPTIONS.md`.

## Project Structure

```
thermal_model/
├── README.md                  # This file
├── ASSUMPTIONS.md             # Heat-source and boundary inputs with citations
├── main.py                    # Entry point; runs the analysis, writes report figures
├── requirements.txt           # Python dependencies
├── config/
│   ├── mission_config.py      # Geometry, mesh, profile, timestep, radiative boundary
│   ├── components_config.py   # Payload component layout, loads, and limits
│   └── thermal_design.py      # Non-component solids: PETG shelves, optical windows
├── src/
│   ├── block_a.py             # External environment + forced convection
│   ├── block_b.py             # 1D implicit wall conduction (+ radiation)
│   ├── block_c.py             # 2D planar finite-volume internal solver
│   ├── coupling.py            # Time-stepping loop coupling the three blocks
│   ├── mesh.py                # Mesh and material/source map assembly
│   ├── mesh_viz.py            # Material and heat-source map rendering
│   ├── materials.py           # Material property database
│   └── postprocessing.py      # Plots and energy-balance diagnostics
├── tests/
│   ├── test_block_a.py
│   ├── test_block_b.py
│   ├── test_block_c.py
│   └── test_energy_conservation.py
└── report_16km/               # Flight-readiness report (OBC powered at 16 km) + figures
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the simulation

```bash
python main.py
```

Run from the `thermal_model/` directory. The analysis evaluates the operating concept in
which the on-board computer is powered on reaching the 16 km imaging altitude, writing
`temperature_contour.png`, `component_temperatures.png`, and `environment.png` into
`report_16km/`. A per-component min/max temperature summary with cold-side margins is
printed to the console.

### Run the tests

```bash
python -m pytest tests/ -v
```

## Report

`report_16km/` contains the flight-readiness report (LaTeX source, compiled PDF, and the
figures it references). Build with:

```bash
pdflatex LHAB_Thermal_FRR_16km_v2.tex   # in report_16km/
```

## Configuration

Design inputs are controlled via the configuration files; the solver code is not modified
for routine studies.

- `config/mission_config.py`: enclosure geometry, mesh resolution, altitude/velocity
  profile, timestep, initial temperature, and the radiative boundary (`EXT_RADIATION`).
- `config/components_config.py`: component layout on the mesh, steady dissipation, and
  operating limits.
- `config/thermal_design.py`: PETG support shelves and optical windows.
