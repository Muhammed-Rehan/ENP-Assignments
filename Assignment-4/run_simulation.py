"""
Run the whole project:

    python run_simulation.py                # writes figures + CSVs to ./results
    python run_simulation.py --length 25    # change the design bus length
    python run_simulation.py --show         # also open the figures

Steps
  0. self-checks (model vs closed form, and the slide-24 table)
  1. waveforms of sharp / RC / ramp / ladder edges against the thresholds
  2. Tqual_sign vs RC time constant and vs slope-control ramp time
  3. distributed RC line: Tqual_sign vs cable length and slope setting
  4. bit-time budget: Tqual_sign -> lost metres -> max bus length per bit rate
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

import bit_budget as bb
import config as cfg
from edge_models import (
    delays_from_waveform,
    ladder_delays,
    ladder_response,
    ramp_delays,
    ramp_input,
    single_pole_delays,
    single_pole_response,
    first_crossing,
)

TH = cfg.THRESHOLDS
V = cfg.V_PROP_M_PER_NS


# ---------------------------------------------------------------------------
# 0. Self-checks
# ---------------------------------------------------------------------------
def self_checks() -> None:
    print("Self-checks")

    # (a) crossing finder reproduces the closed forms for a single pole
    tau = 37.0
    t = np.linspace(0, 600, 60001)
    num = delays_from_waveform(t, single_pole_response(t, tau), TH)
    ana = single_pole_delays(tau, TH)
    assert abs(num.rise_ns - ana.rise_ns) < 0.01 and abs(num.fall_ns - ana.fall_ns) < 0.01
    print(f"  single pole, tau={tau} ns: rise {ana.rise_ns:.2f} ns, fall {ana.fall_ns:.2f} ns  OK")

    # (b) the same for a linear ramp
    tr = 120.0
    num = delays_from_waveform(t, ramp_input(t, tr), TH)
    ana = ramp_delays(tr, TH)
    assert abs(num.rise_ns - ana.rise_ns) < 0.01 and abs(num.fall_ns - ana.fall_ns) < 0.01
    print(f"  ramp, t_r={tr} ns: rise {ana.rise_ns:.2f} ns, fall {ana.fall_ns:.2f} ns  OK")

    # (c) a 1-section ladder must equal a single pole with tau = C * (R0 || RL)
    p1 = cfg.LINE.with_length(10.0)
    p1 = type(p1)(**{**p1.__dict__, "n_sections": 1})
    r0 = p1.r_driver_ohm + p1.r_ohm_per_m * p1.length_m
    cap = (p1.c_pf_per_m * p1.length_m + p1.c_node_pf) * 1e-12
    tau1 = cap * (r0 * p1.r_load_ohm / (r0 + p1.r_load_ohm)) * 1e9
    lad = ladder_delays(p1, 0.0, TH)
    ref = single_pole_delays(tau1, TH)
    assert abs(lad.fall_ns - ref.fall_ns) / ref.fall_ns < 0.01
    print(f"  1-section ladder vs single pole (tau={tau1:.2f} ns): "
          f"{lad.fall_ns:.2f} vs {ref.fall_ns:.2f} ns  OK")

    # (d) the ladder converges as sections are added
    d20 = ladder_delays(type(cfg.LINE)(**{**cfg.LINE.__dict__, "n_sections": 20}), 0.0, TH)
    d80 = ladder_delays(type(cfg.LINE)(**{**cfg.LINE.__dict__, "n_sections": 80}), 0.0, TH)
    assert abs(d20.fall_ns - d80.fall_ns) / d80.fall_ns < 0.02
    print(f"  ladder convergence, 20 vs 80 sections: {d20.fall_ns:.2f} vs {d80.fall_ns:.2f} ns  OK")

    # (e) bit-budget reproduces slide 24 (30, 80, 180, 380, 980 m)
    expected = {1000: 30, 500: 80, 250: 180, 125: 380, 50: 980}
    for br, want in expected.items():
        got = bb.max_length_m(br)
        assert abs(got - want) < 1e-6, (br, got, want)
    print("  slide-24 table (30/80/180/380/980 m)  OK")

    # (f) slide-23 worked example: 600 ns at tq = 125 ns -> 5 tq
    assert bb.prop_seg_tq(bb.prop_seg_min_ns(40.0), 125.0) == 5
    print("  slide-23 example (40 m, tq=125 ns -> 5 tq)  OK\n")


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------
def add_metre_axis(ax, label="equivalent lost cable (m, one-way)"):
    sec = ax.secondary_yaxis("right", functions=(lambda t: t * V, lambda m: m / V))
    sec.set_ylabel(label)
    return sec


# ---------------------------------------------------------------------------
# 1. Waveforms
# ---------------------------------------------------------------------------
def fig_waveforms(plt, out: Path) -> None:
    t = np.linspace(-10, 260, 5401)
    tau, tr = cfg.EXAMPLE_TAU_NS, cfg.EXAMPLE_TR_NS

    def lad(t_ramp):
        tl, yl = ladder_response(cfg.LINE, t_ramp)
        return np.interp(t, tl, yl), delays_from_waveform(tl, yl, TH)

    y_lad, d_lad = lad(0.0)
    y_lad_s, d_lad_s = lad(tr)

    curves = [
        ("Ideal sharp edge", ramp_input(t, 0.0), delays_from_waveform(t, ramp_input(t, 0.0), TH),
         dict(color="0.45", ls="--", drawstyle="steps-post")),
        (f"Single-pole RC, tau = {tau:g} ns", single_pole_response(t, tau), single_pole_delays(tau, TH),
         dict(color="tab:blue")),
        (f"Slope-controlled driver, t_r = {tr:g} ns", ramp_input(t, tr), ramp_delays(tr, TH),
         dict(color="tab:orange")),
        (f"RC ladder, {cfg.LINE.length_m:g} m line, sharp driver", y_lad, d_lad,
         dict(color="tab:green")),
        (f"RC ladder + slope control t_r = {tr:g} ns", y_lad_s, d_lad_s,
         dict(color="tab:red")),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=False)
    for ax, edge in zip(axes, ("rise", "fall")):
        v_th = TH.v_rise if edge == "rise" else TH.v_fall
        for label, y, d, style in curves:
            volts = TH.v_dom * (y if edge == "rise" else 1.0 - y)
            dt = max(d.rise_ns if edge == "rise" else d.fall_ns, 0.0)
            ax.plot(t, volts, lw=1.8, label=f"{label}  ->  {dt:.0f} ns", **style)
            ax.plot(dt, v_th, "o", ms=5, color=style["color"])
        ax.axhline(v_th, color="k", lw=1, ls=":")
        ax.axvline(0, color="0.8", lw=1)
        ax.set_xlabel("time since driver command (ns)")
        ax.set_ylabel("differential voltage CANH - CANL (V)")
        ax.set_xlim(-10, 260)
        ax.grid(alpha=0.25)
    axes[0].set_title(f"Recessive -> dominant (receiver threshold {TH.v_rise} V)")
    axes[1].set_title(f"Dominant -> recessive (receiver threshold {TH.v_fall} V)")
    axes[0].text(250, TH.v_rise + 0.04, "threshold", ha="right", fontsize=8)
    axes[1].text(250, TH.v_fall + 0.04, "threshold", ha="right", fontsize=8)
    axes[0].legend(fontsize=7.5, loc="lower right", title="threshold crossing time = extra delay",
                   title_fontsize=8)
    fig.suptitle("A rounded edge crosses the receiver threshold late: that lateness is Tqual_sign",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "fig1_waveforms.png", dpi=170)


# ---------------------------------------------------------------------------
# 2. Tqual vs tau and t_r
# ---------------------------------------------------------------------------
def fig_simple_sweeps(plt, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    t = np.linspace(0, 1500, 150001)

    # (a) single pole
    taus = np.linspace(*cfg.TAU_SWEEP_NS, 100)
    r = [single_pole_delays(x, TH) for x in taus]
    ax = axes[0]
    ax.plot(taus, [d.fall_ns for d in r], color="tab:red", label="dominant -> recessive (analytic)")
    ax.plot(taus, [d.rise_ns for d in r], color="tab:blue", label="recessive -> dominant (analytic)")
    pts = np.linspace(*cfg.TAU_SWEEP_NS, 9)
    num = [delays_from_waveform(t, single_pole_response(t, x), TH) for x in pts]
    ax.plot(pts, [d.fall_ns for d in num], "o", color="tab:red", mfc="none", label="simulated crossing")
    ax.plot(pts, [d.rise_ns for d in num], "o", color="tab:blue", mfc="none")
    ax.set_xlabel("RC time constant tau (ns)")
    ax.set_ylabel("Tqual_sign (ns)")
    ax.set_title("(a) Single-pole RC rounding")
    add_metre_axis(ax)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    # (b) linear ramp
    trs = np.linspace(*cfg.TR_SWEEP_NS, 100)
    r = [ramp_delays(x, TH) for x in trs]
    ax = axes[1]
    ax.plot(trs, [d.fall_ns for d in r], color="tab:red", label="dominant -> recessive (analytic)")
    ax.plot(trs, [d.rise_ns for d in r], color="tab:blue", label="recessive -> dominant (analytic)")
    pts = np.linspace(*cfg.TR_SWEEP_NS, 9)
    num = [delays_from_waveform(t, ramp_input(t, x), TH) for x in pts]
    ax.plot(pts, [d.fall_ns for d in num], "o", color="tab:red", mfc="none", label="simulated crossing")
    ax.plot(pts, [d.rise_ns for d in num], "o", color="tab:blue", mfc="none")
    ax.set_xlabel("slope-control ramp time t_r (ns)")
    ax.set_ylabel("Tqual_sign (ns)")
    ax.set_title("(b) Slope-controlled driver (linear ramp)")
    add_metre_axis(ax)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle("Slower edge -> later threshold crossing (with these thresholds the falling edge limits)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "fig2_tqual_sweeps.png", dpi=170)


# ---------------------------------------------------------------------------
# 3. Distributed ladder
# ---------------------------------------------------------------------------
def fig_ladder(plt, out: Path) -> dict:
    lengths = cfg.LENGTH_SWEEP_M
    slopes_a = [0.0, cfg.EXAMPLE_TR_NS]
    grid = {}   # (length, t_r) -> EdgeDelays
    for L in lengths:
        for tr in set(slopes_a + cfg.SLOPE_SETTINGS_NS):
            grid[(L, tr)] = ladder_delays(cfg.LINE.with_length(L), tr, TH)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    ax = axes[0]
    for tr, c in zip(slopes_a, ("tab:green", "tab:red")):
        ax.plot(lengths, [grid[(L, tr)].t_qual_ns for L in lengths], "o-", color=c,
                label=f"RC ladder, driver t_r = {tr:g} ns")
    ax.plot(lengths, [L / V for L in lengths], "--", color="0.4",
            label="for scale: cable propagation delay Tmed = L / v")
    ax.set_xlabel("cable length (m)")
    ax.set_ylabel("Tqual_sign (ns)")
    ax.set_title("(a) The cable's own RC rounding grows with length")
    add_metre_axis(ax)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1]
    trs = np.linspace(0, cfg.TR_SWEEP_NS[1], 13)
    for L, c in zip(cfg.LENGTH_SWEEP_SLOPES_NS, ("tab:blue", "tab:orange", "tab:purple")):
        ys = [ladder_delays(cfg.LINE.with_length(L), x, TH).t_qual_ns for x in trs]
        ax.plot(trs, ys, "o-", ms=4, color=c, label=f"RC ladder, {L:g} m")
    ax.plot(trs, [ramp_delays(x, TH).t_qual_ns for x in trs], "--", color="k",
            label="driver ramp alone (no line)")
    ax.set_xlabel("slope-control ramp time t_r (ns)")
    ax.set_ylabel("Tqual_sign (ns)")
    ax.set_title("(b) Line rounding and slope control add up")
    add_metre_axis(ax)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle("Distributed RC line + slope-controlled driver", fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "fig3_distributed_rc.png", dpi=170)
    return grid


# ---------------------------------------------------------------------------
# 4. Bit-time budget
# ---------------------------------------------------------------------------
def fig_budget_and_tables(plt, out: Path, design_len: float) -> None:
    line = cfg.LINE.with_length(design_len)
    rows = []
    for tr in cfg.SLOPE_SETTINGS_NS:
        d = ladder_delays(line, tr, TH)
        rows.append((tr, d))

    # ---- summary table (console + CSV)
    tq500 = 125.0   # time quantum of the slide-23 example (500 kbit/s, 16 tq)
    header = ["t_r_ns", "t_rise_cross_ns", "t_fall_cross_ns", "Tqual_sign_ns", "skew_ns",
              "lost_metres", "propseg_500k_ns", "propseg_500k_tq", "Lmax_500k_m", "Lmax_1M_m"]
    table = []
    for tr, d in rows:
        ps = bb.prop_seg_min_ns(design_len, d.t_qual_ns)
        table.append([tr, d.rise_ns, d.fall_ns, d.t_qual_ns, d.skew_ns,
                      bb.lost_metres(d.t_qual_ns), ps, bb.prop_seg_tq(ps, tq500),
                      bb.max_length_m(500, d.t_qual_ns), bb.max_length_m(1000, d.t_qual_ns)])
    with open(out / "edge_delay_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows([[f"{v:.2f}" if isinstance(v, float) else v for v in r] for r in table])

    print(f"Design bus: {design_len:g} m, RC ladder with {cfg.LINE.n_sections} sections, "
          f"baseline T_elec = {cfg.T_ELEC_BASE_NS:g} ns")
    print(f"{'t_r':>6} {'rise':>7} {'fall':>7} {'Tqual':>7} {'skew':>6} {'lost m':>7} "
          f"{'PROP@500k':>10} {'tq':>3} {'Lmax500k':>9} {'Lmax1M':>7}")
    for r in table:
        print(f"{r[0]:6.0f} {r[1]:7.1f} {r[2]:7.1f} {r[3]:7.1f} {r[4]:6.1f} {r[5]:7.1f} "
              f"{r[6]:10.0f} {r[7]:3d} {r[8]:9.1f} {r[9]:7.1f}")
    print()

    # ---- max length vs bit rate
    rates = cfg.BIT_RATES_KBPS
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    ref = [bb.max_length_m(b) for b in rates]
    ax.plot(rates, ref, "k--", marker="s", label="slide 24 (no edge penalty)")
    colors = plt.cm.viridis(np.linspace(0.0, 0.85, len(rows)))
    csv_rows = []
    for (tr, d), c in zip(rows, colors):
        lm = [bb.max_length_m(b, d.t_qual_ns) for b in rates]
        csv_rows.append([tr, f"{d.t_qual_ns:.2f}"] + [f"{x:.1f}" for x in lm])
        label = f"t_r = {tr:g} ns  (Tqual {d.t_qual_ns:.0f} ns = {bb.lost_metres(d.t_qual_ns):.0f} m)"
        ax.plot(rates, [x if x > 0 else np.nan for x in lm], "o-", color=c, label=label)
        lost_pct = [100.0 * (1.0 - x / r) for x, r in zip(lm, ref)]
        ax2.plot(rates, lost_pct, "o-", color=c, label=label)
        for b, x in zip(rates, lm):
            if x <= 0:
                ax.annotate("x", (b, 1.2), ha="center", color=c, fontsize=11, fontweight="bold")
    ax.axhline(design_len, color="tab:red", ls=":", lw=1.5)
    ax.text(rates[0], design_len * 1.08, f"required length {design_len:g} m", color="tab:red", fontsize=9)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1, 1500)
    ax.set_xticks(rates)
    ax.set_xticklabels([str(r) for r in rates])
    ax.set_xlabel("bit rate (kbit/s)")
    ax.set_ylabel("maximum bus length (m)")
    ax.set_title("(a) Maximum bus length   (x = no valid length)", fontsize=10)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=7.5, loc="upper right")

    ax2.set_xscale("log")
    ax2.set_xticks(rates)
    ax2.set_xticklabels([str(r) for r in rates])
    ax2.minorticks_off()
    ax2.set_ylim(-2, 104)
    ax2.set_xlabel("bit rate (kbit/s)")
    ax2.set_ylabel("reach lost compared with slide 24 (%)")
    ax2.set_title("(b) Tqual is a fixed time cost, so it hurts more as the bit gets shorter", fontsize=10)
    ax2.grid(alpha=0.25)

    fig.suptitle(f"Edge rounding in the bit-time budget  (Tqual from the RC ladder at {design_len:g} m)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "fig4_max_length_vs_bitrate.png", dpi=170)

    with open(out / "max_length_vs_bitrate.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_r_ns", "Tqual_ns"] + [f"Lmax_{b}kbps_m" for b in rates])
        w.writerow(["slide24_reference", 0] + [f"{x:.1f}" for x in ref])
        w.writerows(csv_rows)


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--length", type=float, default=cfg.DESIGN_LENGTH_M, help="design bus length in metres")
    ap.add_argument("--outdir", default="results", help="output folder")
    ap.add_argument("--show", action="store_true", help="open figures interactively")
    args = ap.parse_args()

    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    self_checks()
    fig_waveforms(plt, out)
    fig_simple_sweeps(plt, out)
    grid = fig_ladder(plt, out)
    fig_budget_and_tables(plt, out, args.length)

    # ladder length-sweep table (CSV)
    with open(out / "ladder_length_sweep.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["length_m", "t_r_ns", "t_rise_ns", "t_fall_ns", "Tqual_ns", "lost_metres"])
        for (L, tr), d in sorted(grid.items()):
            w.writerow([L, tr, f"{d.rise_ns:.2f}", f"{d.fall_ns:.2f}", f"{d.t_qual_ns:.2f}",
                        f"{bb.lost_metres(d.t_qual_ns):.2f}"])

    print(f"Figures and CSVs written to {out.resolve()}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
