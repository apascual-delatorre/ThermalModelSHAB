# LHAB Thermal Model

## Purpose

A design tool for high-altitude balloon (LHAB) payload thermal management. It is a
preliminary model suitable for design iteration and trade studies, not a high-fidelity
qualification tool.

## Overview

The model couples three thermal blocks, advanced with a lagged coupling each timestep:

- **Block A**: US Standard Atmosphere 1976 + Churchill-Bernstein cross-flow convection
  (external environment).
- **Block B**: 1D implicit wall conduction for the side wall, end caps, and optical
  windows (enclosure structure). The internal convective coefficient is altitude
  dependent, `h_inside(h) = h0 * sqrt(P(h)/P0)`.
- **Block C**: 2D axisymmetric finite-volume sparse solver for the internal field
  (payload components).

## Project Structure

```
thermal_model/
├── README.md                  # This file
├── main.py                    # Entry point; runs both OBC scenarios, writes report figures
├── requirements.txt           # Python dependencies
├── config/
│   ├── mission_config.py      # Geometry, mesh, altitude/velocity profile, timestep
│   ├── components_config.py   # Payload component layout, loads, and limits
│   └── thermal_design.py      # Non-component solids: PETG frame, optical windows
├── src/
│   ├── block_a.py             # External environment + forced convection
│   ├── block_b.py             # 1D implicit wall conduction
│   ├── block_c.py             # 2D axisymmetric finite-volume internal solver
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
├── report/                    # FRR master document and its figures
├── report_launch/             # Standalone FRR report: OBC powered from launch (+ figures)
├── report_16km/               # Standalone FRR report: OBC powered at 16 km (+ figures)
└── archive/                   # Previous-session outputs and superseded reports
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

Run from the `thermal_model/` directory. Two operating scenarios are evaluated:

- **OBC from launch** &rarr; figures written to `report_launch/`
- **OBC from 16 km** &rarr; figures written to `report_16km/`

Each scenario writes its `temperature_contour.png` and `component_temperatures.png`; the
shared `mesh_map.png` and `environment.png` are written to both folders. A per-component
min/max temperature summary with cold-side margins is printed to the console.

### Run the tests

```bash
python -m pytest tests/ -v
```

## Reports

`report_launch/` and `report_16km/` each contain a complete, self-contained
flight-readiness report (LaTeX source, compiled PDF, and all figures it references).
They are independent so that either can be folded into the master FRR
(`report/LHAB_Thermal_FRR.tex`) once the OBC power-on concept is selected. Build with:

```bash
pdflatex LHAB_Thermal_FRR_Launch.tex   # in report_launch/
pdflatex LHAB_Thermal_FRR_16km.tex     # in report_16km/
```

## Configuration

Design inputs are controlled via the configuration files; the solver code is not modified
for routine studies.

- `config/mission_config.py`: enclosure geometry, mesh resolution, altitude/velocity
  profile, timestep, and initial temperature.
- `config/components_config.py`: component layout on the mesh, steady dissipation, and
  operating limits.
- `config/thermal_design.py`: PETG divider frame and optical windows.

## Current Limitations

The model does not include:

- Radiation heat transfer
- Solar loading
- Curvature effects on wall conduction (planar approximation)
- Battery electrochemical model (resistive heating only)

## Notes

This model prioritises design flexibility and iteration speed. Use it for conceptual
design and sensitivity analysis; validate critical results with higher-fidelity tools or
testing before final design decisions.
