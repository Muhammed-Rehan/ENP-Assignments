"""
Bit-time budget (course slides 21-24): turning an edge delay into metres.

Slide 23:  PROP_SEG_min >= 2 * (Tmed + Tsd + Ttx + Trx + Tqual_sign)
Slide 24:  L_max = v_prop * [ x / (2 * bit_rate) - T_elec ]

Tqual_sign sits inside the same bracket as the cable delay Tmed = L / v_prop,
so a delay of Tqual nanoseconds costs exactly the same one-way budget as
Tqual * v_prop metres of cable.
"""

from __future__ import annotations

import math

import config


def bit_time_ns(bitrate_kbps: float) -> float:
    return 1e6 / bitrate_kbps


def lost_metres(t_ns: float, v_m_per_ns: float = config.V_PROP_M_PER_NS) -> float:
    """Equivalent cable length consumed by an extra one-way delay."""
    return t_ns * v_m_per_ns


def prop_seg_min_ns(
    length_m: float,
    t_qual_extra_ns: float = 0.0,
    t_elec_ns: float = config.T_ELEC_BASE_NS,
    v_m_per_ns: float = config.V_PROP_M_PER_NS,
) -> float:
    """Minimum propagation segment (slide 23)."""
    return 2.0 * (length_m / v_m_per_ns + t_elec_ns + t_qual_extra_ns)


def prop_seg_tq(prop_ns: float, tq_ns: float) -> int:
    """Propagation segment in time quanta, always rounded up (slide 23)."""
    return math.ceil(prop_ns / tq_ns - 1e-9)


def max_length_m(
    bitrate_kbps: float,
    t_qual_extra_ns: float = 0.0,
    x: float = config.PROP_FRACTION,
    t_elec_ns: float = config.T_ELEC_BASE_NS,
    v_m_per_ns: float = config.V_PROP_M_PER_NS,
) -> float:
    """Maximum bus length (slide 24); 0 if the budget is already exhausted."""
    one_way_budget = x * bit_time_ns(bitrate_kbps) / 2.0
    return max(one_way_budget - t_elec_ns - t_qual_extra_ns, 0.0) * v_m_per_ns
