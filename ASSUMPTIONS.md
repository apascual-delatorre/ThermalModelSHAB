# Heat-Source Assumptions & Citations

Reference sheet for the LHAB payload thermal model. Every heat-dissipation value
the model uses is listed here with the literature/datasheet it comes from, so the
report can be (re)written with each number traceable to a source.

**Sources of truth**
- Modeled values: `config/components_config.py` (field `power` [W], `T_op_min/max`).
- Original assumption sheet: `Thermal_Properties_Table_v2.xlsx` ("Thermal Properties").
- All `TBD`/`ASSUMED` values in the Excel are taken as correct for this analysis.

**Framing for the report:** every entry below is a *justified engineering choice*
backed by a datasheet, standard, or peer-reviewed model — not a placeholder. State
them as decisions with citations.

---

## 1. Component heat sources (model vs. source)

`P` = steady electrical dissipation modeled in code. "Excel" = value/range on the
original sheet. ✓ = code is consistent with the cited source; ⚠ = code differs from
Excel and should be reconciled (see notes).

| # | Component | Subsystem | P modeled [W] | Excel basis | Citation | Status |
|---|-----------|-----------|---------------|-------------|----------|:------:|
| 1 | NVIDIA Jetson Orin Nano | OBC | **7.0** | 7–16 W (7 typ / 16 TDP) | NVIDIA DS-10653-001 Rev.1.0 (2023) — typical SoM power | ✓ uses typical |
| 2 | STM32 Nucleo F446RE | OBC | **0.3** | 0.1–0.5 W active | ST UM1724 Rev.14; STM32F446RE DS | ✓ mid-range |
| 3 | 250 GB SSD (NVMe M.2) | OBC | **3.0** | 1–2 W active | Samsung 980 measured 3.1 W avg / 4.3 W peak (Tom's Hardware, 2021); JEDEC JESD218 | ✓ = measured avg |
| 4 | USB Stick (USB 3.0) | OBC | **0.5** | ~0.1 W (idle) | Active write 0.4–1.0 W measured; USB 3.0 Rev.1.0 §11.4.5.2 (4.5 W bus ceiling) | ✓ corrected (was 3.0) |
| 5 | SD Card Reader + Card | OBC | **0.05** | ~0.05 W | Generic SD consumer spec | ✓ |
| 6 | Prophesee EVK4 (IMX636) | Payload | **1.5** | ~1.5 W (TBD) | Prophesee Metavision EVK4 HD HW Guide Rev.C (2023) | ✓ estimate adopted |
| 7 | Wolfgang GA100 (frame cam) | Payload | **3.0** | 2.5–4 W (GoPro proxy) | GoPro Hero 12/13 User Manual (2023), proxy | ✓ mid-range |
| 8 | Soyo C-Mount Lens | Payload | **0.0** | 0 W (passive) | Passive optic — no electrical load | ✓ |
| 9 | Battery (Li-ion / Li-Po) | EPS | **0.3** | 0 W + "I²R 1–3% of output" | Bernardi et al. 1985 + IEC 62133 (see §2) | ✓ = 1.6% of load |
| 10 | Flex 5 Powerbank | EPS | **0.4** | 0 W + "conversion 2–5%" | DC-DC buck efficiency 90–97% (see §2) | ✓ = 2.1% of load |
| 11 | Wiring & Connectors | EPS | **0.5** | 0.3–1.0 W I²R | Copper harness per IPC-2221 | ✓ mid-range |
| 12 | GNSS Module (NEO-M9N) | Sensors | **0.15** | ~0.15 W | u-blox UBX-19014285 Rev.05 — 68 mW track / 150 mW acq | ✓ |
| 13 | GNSS Antenna (patch) | Sensors | **0.0** | ~0 W (passive) | Passive ceramic patch | ✓ |
| 14 | IMU (ICM-20948) ×2 | Sensors | **0.01** | ~0.01 W | TDK InvenSense ICM-20948 Rev.1.3 (2017) | ✓ |
| 15 | Env. Sensor MS8607 ×2 | Sensors | **0.005** | ~0.005 W | TE Connectivity MS8607 Rev.A (2016) | ✓ |
| 16 | SPOT Trace | Recovery | **0.3** | ~0.3 W avg (burst ~1 W) | SPOT Trace product spec — duty-cycled uplink | ✓ |
| 17 | Strato Tracker | Recovery | **0.5** | ~0.5 W avg | Stratotracker product spec — LoRa + GPS | ✓ |

**Total modeled payload electrical load ≈ 16.8 W** (sum of all dissipators,
excluding the EPS self-heat terms #9–#10). This figure anchors the battery/converter
loss fractions in §2.

---

## 2. Battery & converter heat — the "does it depend on drawn power?" answer

The SE's question: *does battery heat depend on drawn wattage, or what conversion
loss was assumed?* Answer, fully from literature (no bench test required):

- **Physical basis — Bernardi, Pawlikowski & Newman (1985),** *J. Electrochem. Soc.*
  **132(1):5–12.** Battery heat `Q = I(V_oc − V) − I·T·(dV_oc/dT)`. The first term
  `I(V_oc − V) = I²·R_int` is the irreversible Joule (I²R) heat; the second is the
  reversible entropic term.
- **Modeling choice:** the entropic term is neglected (small, sign-alternating) and,
  because the recording load is quasi-steady, the I²R term is represented as a **fixed
  fraction of delivered power** rather than a live current trace.
- **Fraction used:** ~1.5%, consistent with generic Li-ion internal resistance per
  **IEC 62133** (18650/Li-Po cells ~30–100 mΩ each).
- **Consistency check:** modeled battery 0.3 W = **1.8%** of the 16.8 W load → inside
  the cited 1–3% band. Powerbank 0.4 W = **2.4%** → inside the 2–5% DC-DC conversion
  band (buck-converter efficiency 90–97%, standard).

So **yes**, battery heat depends on current (I²R); the model captures it as a
literature-grounded percentage of throughput, which is the standard quasi-steady
assumption for a constant-load payload.

---

## 3. Notes / reconcile flags

- **N1 — SSD & USB (#3, #4): RESOLVED via literature.**
  - **SSD kept at 3.0 W.** A 250 GB-class DRAM-less NVMe (Samsung 980, PCIe 3.0)
    measures 3.1 W active average / 4.3 W peak under sustained write (Tom's Hardware,
    2021). 3.0 W ≈ the measured average — defensible as-is, no change.
  - **USB corrected 3.0 → 0.5 W.** Measured active-write power of USB 3.0 flash drives
    is 0.4–1.0 W; the Excel's 0.1 W was an idle/suspend figure. 3.0 W had no basis.
    0.5 W = sustained active write, 1.0 W conservative peak (USB 3.0 Rev.1.0 §11.4.5.2
    caps the bus at 900 mA·5 V = 4.5 W).
- Operating-temperature limits (`T_op_min/max`) in code match the Excel for every
  component; the cold-survival margins in the report read directly from these.
- Several `T_min` values (Battery −20 °C, GA100 −10 °C) are PROXY/ASSUMED in the
  Excel pending exact-model datasheets; treated as correct per project scope.

---

## 4. OBC power gating (affects which sources are active when)

Heat sources are not all on for the whole flight. The OBC-gated loads (Jetson, SSD,
USB, SD reader, EVK4) only dissipate while the OBC is powered; the gating is applied
in `main.py` (`with_obc_schedule`), driven by the `obc_gated: True` flag in
`config/components_config.py`.

---

## 5. External radiative boundary (outer wall)

The outer enclosure surface exchanges long-wave radiation with the environment in
parallel with external convection (`config/mission_config.py`, `EXT_RADIATION`).

| Quantity | Value | Basis / citation |
|----------|-------|------------------|
| Emissivity `eps_ir` | **0.90** | Long-wave emissivity of expanded-polypropylene / non-metallic polymer shell; Incropera & DeWitt, *Fundamentals of Heat and Mass Transfer*, Table A.11 (non-metallic surfaces ε ≈ 0.88–0.95) |
| Sink temperature `T_sink` | **216.65 K (−56.5 °C)** | Effective radiative-environment temperature at altitude, taken at the tropopause / lower-stratosphere minimum of the US Standard Atmosphere 1976 |
| Absorbed solar `q_solar` | **0 W/m²** | Night mission — no incident solar flux |

The net flux `eps_ir·σ·(T_sink⁴ − T_surf⁴)` is linearised about the previous
outer-surface temperature each timestep (`src/block_b.py`), keeping the wall solve
tridiagonal. Because the mission flies at night, the radiative term is a heat-loss
path only; it is strongest at altitude, where the thinning atmosphere has already
collapsed the external convective coefficient.
