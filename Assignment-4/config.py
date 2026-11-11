"""
Central configuration for the CAN edge-rounding simulation.

Every number the simulation depends on lives here, so you can change a
scenario without touching the model code.  Values marked (slides) come from
the Unit-2 deck (slides 21-24); values marked (assumed) are illustrative and
should be replaced with your own cable / transceiver datasheet numbers.
"""

from edge_models import LineParams, Thresholds

# --------------------------------------------------------------------------
# Bit-time budget  (slides 21-24)
# --------------------------------------------------------------------------
V_PROP_M_PER_NS = 0.2      # twisted pair, 0.2 m/ns = 5 ns per metre   (slides)
T_ELEC_BASE_NS = 100.0     # Tsd+Ttx+Trx+Tqual for a clean square edge (slides)
PROP_FRACTION = 0.5        # x = share of the bit given to PROP_SEG    (slides)
BIT_RATES_KBPS = [50, 125, 250, 500, 1000]

# --------------------------------------------------------------------------
# Receiver thresholds  (ISO 11898-2, differential voltage CANH - CANL)
# --------------------------------------------------------------------------
THRESHOLDS = Thresholds(
    v_dom=2.0,    # nominal dominant differential level, V
    v_rise=0.9,   # recessive -> dominant: receiver flips above this
    v_fall=0.5,   # dominant -> recessive: receiver flips below this
)

# --------------------------------------------------------------------------
# Bus model for the distributed-RC ladder  (assumed, illustrative)
# --------------------------------------------------------------------------
DESIGN_LENGTH_M = 40.0     # the worked example on slide 21

LINE = LineParams(
    length_m=DESIGN_LENGTH_M,
    r_ohm_per_m=0.14,      # loop resistance of a twisted pair, ohm/m
    c_pf_per_m=40.0,       # wire-to-wire capacitance, pF/m
    r_driver_ohm=25.0,     # effective driver output resistance, ohm
    r_load_ohm=60.0,       # 2 x 120 ohm terminations as seen by the driver
    c_node_pf=100.0,       # transceiver / connector capacitance, all nodes, pF
    n_sections=40,         # RC sections used to approximate the line
)

# --------------------------------------------------------------------------
# Scenarios to compare
# --------------------------------------------------------------------------
# Slope-control setting = time for the driver output to ramp over the full
# swing.  Convert from a datasheet slew rate with:  t_r = swing / slew_rate.
SLOPE_SETTINGS_NS = [0.0, 25.0, 50.0, 100.0, 150.0, 200.0]

# Examples used for the waveform figure
EXAMPLE_TAU_NS = 40.0      # single-pole RC time constant
EXAMPLE_TR_NS = 100.0      # linear slope-control ramp time

# Sweeps
TAU_SWEEP_NS = (1.0, 100.0)
TR_SWEEP_NS = (1.0, 300.0)
LENGTH_SWEEP_M = [5, 10, 20, 40, 60, 80, 100]
LENGTH_SWEEP_SLOPES_NS = [10.0, 40.0, 100.0]   # lengths shown in fig 3b
