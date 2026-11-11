"""
Edge-rounding models for a CAN differential signal.

Three ways of producing a rounded edge are provided:

1. single_pole_*   - ideal step through one RC low-pass (analytic)
2. ramp_*          - slope-controlled driver, linear ramp (analytic)
3. ladder_*        - N-section RC ladder (a distributed RC line), optionally
                     driven by a slope-limited driver (numerical)

All of them are reduced to the same two numbers per scenario:

    rise_ns : time for a recessive->dominant edge to cross the receiver's
              dominant threshold (default 0.9 V)
    fall_ns : time for a dominant->recessive edge to cross the receiver's
              recessive threshold (default 0.5 V)

measured from the instant the driver *commands* the edge.  For a perfectly
sharp edge both are 0, so these crossing times ARE the extra delay that the
course slides call Tqual_sign.

Everything is linear, so one normalised step response y(t) (0 -> 1) describes
both edges:
    rising  edge: V = Vdom * y(t)        crosses v_rise when y = v_rise/Vdom
    falling edge: V = Vdom * (1 - y(t))  crosses v_fall when y = 1 - v_fall/Vdom
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm


# ---------------------------------------------------------------------------
# Thresholds and results
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Thresholds:
    v_dom: float = 2.0     # dominant differential level, V
    v_rise: float = 0.9    # receiver reads "dominant" above this, V
    v_fall: float = 0.5    # receiver reads "recessive" below this, V

    @property
    def y_rise(self) -> float:
        """Level of the normalised step response at the rising-edge crossing."""
        return self.v_rise / self.v_dom

    @property
    def y_fall(self) -> float:
        """Level of the normalised step response at the falling-edge crossing."""
        return 1.0 - self.v_fall / self.v_dom


@dataclass(frozen=True)
class EdgeDelays:
    rise_ns: float
    fall_ns: float

    @property
    def t_qual_ns(self) -> float:
        """Tqual_sign: the worse of the two edges (the one that limits timing)."""
        return max(self.rise_ns, self.fall_ns)

    @property
    def skew_ns(self) -> float:
        """Fall minus rise: pulse-width distortion of a dominant bit."""
        return self.fall_ns - self.rise_ns


# ---------------------------------------------------------------------------
# Threshold crossing
# ---------------------------------------------------------------------------
def first_crossing(t: np.ndarray, y: np.ndarray, level: float) -> float:
    """First time y reaches `level`, by linear interpolation (nan if never)."""
    hit = y >= level
    if not hit.any():
        return float("nan")
    i = int(np.argmax(hit))
    if i == 0:
        return float(t[0])
    t0, t1, y0, y1 = t[i - 1], t[i], y[i - 1], y[i]
    return float(t0 + (level - y0) * (t1 - t0) / (y1 - y0))


def delays_from_waveform(t_ns: np.ndarray, y: np.ndarray, th: Thresholds) -> EdgeDelays:
    """Crossing times of a normalised step response y(t) for both edges."""
    return EdgeDelays(
        rise_ns=first_crossing(t_ns, y, th.y_rise),
        fall_ns=first_crossing(t_ns, y, th.y_fall),
    )


# ---------------------------------------------------------------------------
# 1. Single-pole RC (analytic)
# ---------------------------------------------------------------------------
def single_pole_response(t_ns: np.ndarray, tau_ns: float) -> np.ndarray:
    t = np.asarray(t_ns, dtype=float)
    if tau_ns <= 0:
        return (t >= 0).astype(float)
    return np.where(t >= 0, 1.0 - np.exp(-np.clip(t, 0, None) / tau_ns), 0.0)


def single_pole_delays(tau_ns: float, th: Thresholds) -> EdgeDelays:
    """Closed form:  t = -tau * ln(1 - y_level)."""
    return EdgeDelays(
        rise_ns=-tau_ns * np.log(1.0 - th.y_rise),
        fall_ns=-tau_ns * np.log(1.0 - th.y_fall),
    )


# ---------------------------------------------------------------------------
# 2. Linear slope-controlled driver (analytic)
# ---------------------------------------------------------------------------
def ramp_input(t_ns: np.ndarray, t_ramp_ns: float) -> np.ndarray:
    """Driver command: 0 -> 1 linearly over t_ramp_ns (a step if t_ramp = 0)."""
    t = np.asarray(t_ns, dtype=float)
    if t_ramp_ns <= 0:
        return (t >= 0).astype(float)
    return np.clip(t / t_ramp_ns, 0.0, 1.0)


def ramp_delays(t_ramp_ns: float, th: Thresholds) -> EdgeDelays:
    """Closed form:  t = y_level * t_ramp."""
    return EdgeDelays(rise_ns=th.y_rise * t_ramp_ns, fall_ns=th.y_fall * t_ramp_ns)


def ramp_time_from_slew(slew_v_per_us: float, swing_v: float = 2.0) -> float:
    """Convert a datasheet slew rate (V/us) to a full-swing ramp time (ns)."""
    return swing_v / slew_v_per_us * 1000.0


# ---------------------------------------------------------------------------
# 3. Distributed RC line as an N-section ladder (numerical)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LineParams:
    length_m: float = 40.0
    r_ohm_per_m: float = 0.14      # loop resistance
    c_pf_per_m: float = 40.0       # wire-to-wire capacitance
    r_driver_ohm: float = 25.0     # driver output resistance
    r_load_ohm: float = 60.0       # termination seen by the driver
    c_node_pf: float = 100.0       # lumped node capacitance at the far end
    n_sections: int = 40

    def with_length(self, length_m: float) -> "LineParams":
        return LineParams(**{**self.__dict__, "length_m": float(length_m)})


def ladder_state_space(p: LineParams):
    """
    State-space form  dv/dt = A v + B u  of the ladder.

    Section k = series resistor R_seg followed by shunt capacitor C_seg to
    ground.  The driver resistance is added to the first series resistor, the
    receiver-end node carries the lumped node capacitance, and R_load to ground
    models the terminations.  Input u is the driver's open-circuit voltage
    (0..1); the output is the voltage at the last node.
    """
    n = p.n_sections
    r_seg = p.r_ohm_per_m * p.length_m / n
    c_seg = p.c_pf_per_m * 1e-12 * p.length_m / n

    cap = np.full(n, c_seg)
    cap[-1] += p.c_node_pf * 1e-12
    r = np.full(n, r_seg)
    r[0] += p.r_driver_ohm
    g = 1.0 / r                          # g[k] feeds node k from node k-1 / source

    G = np.zeros((n, n))                 # nodal conductance matrix
    for k in range(n):
        G[k, k] += g[k]
        if k > 0:
            G[k - 1, k - 1] += g[k]
            G[k, k - 1] -= g[k]
            G[k - 1, k] -= g[k]
    G[n - 1, n - 1] += 1.0 / p.r_load_ohm

    b = np.zeros(n)
    b[0] = g[0]

    A = -G / cap[:, None]
    B = b / cap
    dc_gain = float((-np.linalg.solve(A, B))[-1])
    return A, B, dc_gain


def ladder_response(
    p: LineParams, t_ramp_ns: float = 0.0, n_steps: int = 4000
) -> tuple[np.ndarray, np.ndarray]:
    """
    Normalised step response (0 -> 1) at the receiver end of the ladder, with
    the driver command shaped by a linear ramp of t_ramp_ns (0 = sharp step).

    Uses an exact zero-order-hold discretisation (matrix exponential), so the
    result does not depend on stiffness of the ladder's fast modes.
    """
    A, B, dc = ladder_state_space(p)
    n = A.shape[0]

    eig = np.linalg.eigvals(A).real
    tau_slow_s = 1.0 / np.min(np.abs(eig))
    t_end_s = 12.0 * tau_slow_s + 2.0 * t_ramp_ns * 1e-9
    dt = t_end_s / n_steps

    M = np.zeros((n + 1, n + 1))
    M[:n, :n] = A * dt
    M[:n, n] = B * dt
    E = expm(M)
    Ad, Bd = E[:n, :n], E[:n, n]

    t_s = np.arange(n_steps + 1) * dt
    u = ramp_input((t_s[:-1] + 0.5 * dt) * 1e9, t_ramp_ns)   # mid-interval value

    x = np.zeros(n)
    y = np.zeros(n_steps + 1)
    for k in range(n_steps):
        x = Ad @ x + Bd * u[k]
        y[k + 1] = x[-1]
    return t_s * 1e9, y / dc


def ladder_delays(
    p: LineParams, t_ramp_ns: float, th: Thresholds
) -> EdgeDelays:
    t, y = ladder_response(p, t_ramp_ns)
    return delays_from_waveform(t, y, th)
