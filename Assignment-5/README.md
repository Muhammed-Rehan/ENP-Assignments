# CAN Bus: How a Rounded Edge Eats Cable Length

**Course:** Embedded Network Protocols, Unit 2 (The CAN Physical Layer)
**Question:** how much does a slow edge cost, in *metres of cable*, inside the CAN bit-time budget?

A slow (rounded) edge crosses the receiver's threshold later than a sharp one.
That extra lateness is the delay the course slides call **Tqual_sign** (slide 22 unit 2 ppt).
Because Tqual_sign sits in the *same bracket* as the cable delay in the
propagation-segment formula (slide 23), it can be traded one-for-one against
cable length:

```
PROP_SEG_min  >=  2 x ( Tmed + Tsd + Ttx + Trx + Tqual_sign )          (slide 23)

lost cable (one-way)  =  Tqual_sign x v_prop  =  Tqual_sign / 5 ns per metre
```

This project simulates how edge rounding (an RC low-pass, a distributed RC line,
and a slope-controlled driver) delays the threshold crossing, then converts that
delay into lost metres, a longer propagation segment (in time quanta), and a
smaller maximum bus length.

---

## 1. Quick start

```bash
pip install -r requirements.txt        # numpy, scipy, matplotlib
python run_simulation.py               # ~5 s; writes figures + CSVs into ./results
```

Options:

```bash
python run_simulation.py --length 25   # change the design bus length (default 40 m)
python run_simulation.py --outdir out  # write somewhere else
python run_simulation.py --show        # also open the figures interactively
```

Every run starts with six **self-checks** (see section 5); if one fails, the
script stops with an assertion error before producing any results.

## 2. Project layout

```
can_edge_sim/
├── README.md
├── requirements.txt
├── config.py            all parameters (cable, thresholds, slope settings) in one place
├── edge_models.py       edge models: single-pole RC, linear ramp, RC ladder; threshold crossing
├── bit_budget.py        Tqual -> lost metres -> propagation segment -> max bus length
├── run_simulation.py    runs the experiments, self-checks, figures, CSVs
└── results/
    ├── fig1_waveforms.png
    ├── fig2_tqual_sweeps.png
    ├── fig3_distributed_rc.png
    ├── fig4_max_length_vs_bitrate.png
    ├── edge_delay_summary.csv
    ├── ladder_length_sweep.csv
    └── max_length_vs_bitrate.csv
```

## 3. How it works

### 3.1 Edge models (`edge_models.py`)

| Model | What it represents | Method |
|---|---|---|
| Single-pole RC | one lumped R and C rounding an ideal step | closed form `t = -tau * ln(1 - y)` |
| Linear ramp | slope-controlled driver, full swing in `t_r` | closed form `t = y * t_r` |
| RC ladder | distributed RC line: driver resistance, N x (R_seg + C_seg), node capacitance, terminations | state-space model, exact matrix-exponential time stepping |
| Ladder + ramp | slope-controlled driver feeding the line (the realistic case) | same ladder, ramped input |

The system is linear, so one normalised step response `y(t)` (0 to 1) gives both edges:

* recessive to dominant: `V = Vdom * y(t)`, crosses the **0.9 V** dominant threshold when `y = 0.45`
* dominant to recessive: `V = Vdom * (1 - y(t))`, crosses the **0.5 V** recessive threshold when `y = 0.75`

(Receiver thresholds are the usual ISO 11898-2 differential values; `Vdom = 2 V`.
They are set in `config.py`.)

### 3.2 Definition of Tqual_sign

For each scenario the script measures the time, from the instant the driver
*commands* the edge, at which the received differential voltage crosses the
threshold. A perfectly sharp edge crosses at 0 ns, so the crossing time **is** the
extra delay. Two numbers come out:

* `t_rise_cross`: recessive to dominant edge
* `t_fall_cross`: dominant to recessive edge

**Tqual_sign = max(rise, fall).** The later edge is the one that limits timing.
With the default thresholds this is always the falling edge, because 0.5 V
sits near the *end* of the decay while 0.9 V sits well up the rise.
The difference `fall - rise` is reported as **skew** (it distorts the width of a
dominant bit).

### 3.3 From delay to metres (`bit_budget.py`)

| Quantity | Formula | Slide |
|---|---|---|
| Lost cable | `Tqual x v_prop`, with `v_prop = 0.2 m/ns` (5 ns/m) | 21 |
| Minimum propagation segment | `2 x (L/v + T_elec + Tqual)` | 23 |
| Propagation segment in time quanta | `ceil(PROP_SEG / tq)`, must be 1 to 8 | 15, 23 |
| Maximum bus length | `v x [ x/(2 x bit rate) - T_elec - Tqual ]`, with `x = 50 %` | 24 |

**Baseline.** `T_ELEC_BASE_NS = 100 ns` is the slides' "about 100 ns in practice"
for a clean square edge. The simulated Tqual is the **additional** delay from
the rounded edge, on top of that baseline. (If your own 100 ns figure already
contains some typical rounding, the absolute max-length numbers shift slightly,
but the *differences between scenarios*, which are the point of this project,
do not.)

## 4. Results (default parameters)

Design bus: 40 m, 40-section RC ladder (R = 0.14 ohm/m, C = 40 pF/m, driver 25 ohm,
load 60 ohm, 100 pF node capacitance). From `results/edge_delay_summary.csv`:

| Slope setting t_r | Rise (ns) | Fall (ns) | **Tqual_sign (ns)** | Skew (ns) | **Lost cable (m)** | PROP_SEG @500k | Max length @500k | Max length @1M |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 (sharp driver) | 20.3 | 44.9 | **44.9** | 24.6 | **9.0** | 690 ns (6 tq) | 71.0 m | 21.0 m |
| 25 ns | 33.6 | 58.3 | 58.3 | 24.6 | 11.7 | 717 ns (6 tq) | 68.3 m | 18.3 m |
| 50 ns | 48.3 | 73.2 | 73.2 | 24.9 | 14.6 | 746 ns (6 tq) | 65.4 m | 15.4 m |
| 100 ns | 74.9 | 107.3 | 107.3 | 32.4 | 21.5 | 815 ns (7 tq) | 58.5 m | 8.5 m |
| 150 ns | 99.0 | 145.0 | 145.0 | 46.1 | 29.0 | 890 ns (8 tq) | 51.0 m | 1.0 m |
| 200 ns | 122.2 | 182.8 | 182.8 | 60.6 | 36.6 | 966 ns (8 tq) | 43.4 m | **0 m** |

(Time quantum for the PROP_SEG column: 125 ns, i.e. the slides' 500 kbit/s, 16 tq example.)

What the numbers say:

1. **Even a "sharp" driver costs about 9 m** on this 40 m bus (about 1.7 nF of total capacitance), because the cable and node capacitance round the edge.
2. **Slope control adds on top.** At `t_r = 100 ns` the edge costs about 21 m of cable. That is more than half of a 40 m bus.
3. **The damage scales with bit rate**, because Tqual is a fixed time cost taken out of an ever shorter bit (Fig. 4b). At 50 kbit/s it is a rounding error (about 1 to 4 %). At 1 Mbit/s the same edge removes 30 to 100 % of the reach.
4. **At 1 Mbit/s, `t_r = 200 ns` leaves no valid bus length at all**, even though the slide-24 table promises 30 m.
5. **The propagation segment creeps toward its limit.** At 500 kbit/s it grows from 6 to 8 tq, and at 8 tq the 1-to-8 rule (slide 15) leaves no margin.

The same cause shows up on every figure: the later the edge crosses the threshold, the more of the one-way budget it consumes.

### Figures

| File | Shows |
|---|---|
| `fig1_waveforms.png` | rising and falling edges for sharp / RC / ramp / ladder / ladder + ramp, with the threshold crossing marked |
| `fig2_tqual_sweeps.png` | Tqual vs tau and vs t_r, analytic lines with simulated crossings, plus an equivalent-metres axis |
| `fig3_distributed_rc.png` | distributed RC line: Tqual vs cable length and vs slope setting |
| `fig4_max_length_vs_bitrate.png` | maximum bus length per bit rate for each slope setting, and the percentage of reach lost |

## 5. Validation

`run_simulation.py` checks the model before it runs any experiment:

| Check | What is compared |
|---|---|
| a | numerical crossing finder vs the closed form for a single pole |
| b | the same for a linear ramp |
| c | a **1-section ladder** vs a single pole with `tau = C x (R0 \|\| R_load)` |
| d | ladder **convergence**: 20 vs 80 sections agree within 2 % |
| e | the bit-budget code reproduces **slide 24's table** (30 / 80 / 180 / 380 / 980 m) |
| f | the **slide 23 worked example** (40 m, tq = 125 ns gives 5 tq) |

## 6. Parameters you should replace with real values

Everything is in `config.py`. The cable and driver numbers are **illustrative**,
chosen to be plausible for a twisted pair; swap in your own:

| Parameter | Default | Where to get it |
|---|---|---|
| `r_ohm_per_m`, `c_pf_per_m` | 0.14 ohm/m, 40 pF/m | cable datasheet |
| `r_driver_ohm` | 25 ohm | transceiver datasheet (output resistance / drive current) |
| `c_node_pf` | 100 pF | nodes x (transceiver + connector capacitance) |
| `SLOPE_SETTINGS_NS` | 0 to 200 ns | transceiver slope-control (Rs pin) curves |
| `THRESHOLDS` | 0.9 V / 0.5 V | ISO 11898-2 or the transceiver datasheet |

To convert a datasheet slew rate into a ramp time, use
`edge_models.ramp_time_from_slew(slew_v_per_us, swing_v=2.0)`. For example,
10 V/us over a 2 V swing gives `t_r = 200 ns`.

## 7. Limitations (please read before you quote the numbers)

* **The RC ladder is a low-pass approximation, not a transmission-line model.**
  It ignores line inductance and wave propagation. The propagation delay
  `Tmed = L/v` is accounted for *separately* (as the slides do), and the ladder
  only supplies the *edge rounding*. For a 40 m cable the one-way line delay
  (200 ns) is longer than the edge times simulated here, so a real line behaves
  as a transmission line and the ladder's absolute Tqual is a **conservative
  (pessimistic) estimate**, especially for the length sweep in Fig. 3a at 60 to
  100 m. The *trends* (slower edge means later crossing means fewer metres) are
  robust; for absolute numbers, confirm with a transmission-line simulation
  (e.g. an LTspice `T`-line or lossy-line model with 120 ohm terminations).
* **Both terminations are lumped** into one 60 ohm load, and all node capacitance sits at the receiver end (worst case).
* **The driver is a linear source.** Real CAN drivers are non-linear, and the recessive transition is partly passive. In this model the fall/rise asymmetry comes only from the unequal thresholds.
* **Tqual is measured on a single edge** (no data-dependent jitter, no noise, no reflections from stubs).
* **The max-length formula** uses Tqual computed at the design length, not re-solved for each length.
* Slide 24 values are "first-cut numbers", as the slide itself says.

## 8. Ideas for extending it

* Replace the RC ladder with an LTspice transmission-line netlist and compare Tqual.
* Add stubs (backbone topology, slide 19) and show reflections for sharp edges against the cleaner slow edges. This is the *benefit* side of slope control.
* Add an EMI proxy, for example spectral content or `dV/dt` per setting, to plot the trade-off: lost metres against emission reduction.
* Re-solve the maximum length self-consistently, since Tqual depends on length.
* Sweep the sample point and phase segments to see where a late edge starts to violate the bit-timing rules (slides 28 to 29).

## 9. References

* Unit-2 slides, *The CAN Physical Layer* (slides 15, 19, 21 to 24)
* D. Paret, *Multiplexed Networks for Embedded Systems*, Wiley, 2007, chapter 3
* ISO 11898-2 (high-speed CAN physical layer), receiver thresholds
