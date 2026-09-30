# Activity 4.1: CAN Physical Media Selection and Fault Analysis

This repository contains an Embedded C application that evaluates different CAN physical media (Single-wire, Differential Twisted-Pair, and Twisted-Pair with Screen) to determine suitability for automotive and industrial applications based on physical parameters and fault conditions[cite: 1].

---

## Features
* **Physical Media Evaluation**: Analyzes single-wire, differential pair, and shielded twisted-pair CAN configurations[cite: 1].
* **Suitability Verification**: Validates bus length against bit rate according to ISO 11898 constraints, checking termination resistor requirements and bus fault status[cite: 1].
* **Fault Simulation**: Models signal degradation and communication loss caused by open-circuit and short-circuit faults[cite: 1].
* **Extension Comparison**: Evaluates and displays physical-layer characteristics across all available alternative media for comparison[cite: 1].

---

## Input Parameters & Values

| Parameter | Values / Constraints |
| :--- | :--- |
| `media_type` | `1` = Single Wire, `2` = Differential Pair, `3` = Twisted + Screen[cite: 1] |
| `bit_rate` | `125`, `250`, `500`, `1000` kbps[cite: 1] |
| `bus_length` | Bus length in meters[cite: 1] |
| `node_count` | Number of connected CAN nodes[cite: 1] |
| `fault_type` | `0` = No fault, `1` = Open, `2` = Short[cite: 1] |
| `noise_level` | `0` to `100%`[cite: 1] |
| `termination` | `0` = Absent, `1` = Present[cite: 1] |

---

## Expected Output Structure

```text
---------------------------------------------------
                 EVALUATION REPORT                 
---------------------------------------------------
CAN Medium        : Differential Twisted Pair
Wires             : 2
Noise Rejection   : HIGH
Radiation         : LOW
Bit Rate          : 500 kbps
Bus Length        : 100 m
Nodes             : 10
Termination       : OK
Fault Effect      : None
Recommended App   : Powertrain, chassis control, high-speed automotive networks
Bus Status        : SUITABLE

===================================================
       EXTENSION: COMPARISON WITH ALTERNATIVES     
===================================================
[SELECTED] Differential Twisted-Pair CAN
  - Wires: 2
  - Noise Rejection: HIGH
  - Radiation Susceptibility: LOW
  - Recommended Use: Powertrain, chassis control, high-speed automotive networks

[ALTERNATIVE] Single-wire CAN
  - Wires: 1
  - Noise Rejection: LOW
  - Radiation Susceptibility: HIGH
  - Recommended Use: Low-speed body electronics, comfort control

[ALTERNATIVE] Twisted-Pair with Screen
  - Wires: 3
  - Noise Rejection: VERY HIGH
  - Radiation Susceptibility: VERY LOW
  - Recommended Use: Industrial automation, harsh EMI environments

gcc -Wall -o activity1 activity1.c
./activity1