### `README_Activity2.md` (Activity 2)

```markdown
# Activity 2: High-Speed CAN Voltage-Level Monitor

This repository contains an Embedded C simulation of a High-Speed CAN receiver[cite: 2]. The program reads `CAN_H` and `CAN_L` differential voltage levels, computes the differential bus voltage ($V_{diff} = CAN\_H - CAN\_L$), and classifies the CAN bus line state into **Recessive**, **Dominant**, **Boundary**, or **Invalid/Noise Region**[cite: 2].

---

## Key Voltage Definitions & Thresholds

* **Recessive Threshold**: $V_{diff} < 0.5\text{ V}$[cite: 2]
* **Dominant Threshold**: $V_{diff} > 0.9\text{ V}$[cite: 2]
* **Invalid / Noise Region**: $0.5\text{ V} < V_{diff} \le 0.9\text{ V}$[cite: 2]
* **Nominal Recessive Levels**: $CAN\_H = 2.5\text{ V}$, $CAN\_L = 2.5\text{ V}$ ($V_{diff} = 0.0\text{ V}$)[cite: 2]
* **Nominal Dominant Levels**: $CAN\_H = 3.5\text{ V}$, $CAN\_L = 1.5\text{ V}$ ($V_{diff} = 2.0\text{ V}$)[cite: 2]

---

## Verification Test Cases

| `CAN_H (V)` | `CAN_L (V)` | `Vdiff (V)` | Expected Result | Program Output |
| :---: | :---: | :---: | :--- | :--- |
| 2.5 | 2.5 | 0.0 | Recessive[cite: 2] | `RECESSIVE` |
| 3.5 | 1.5 | 2.0 | Dominant[cite: 2] | `DOMINANT` |
| 2.8 | 2.3 | 0.5 | Boundary[cite: 2] | `Boundary (Transition Region)` |
| 3.0 | 2.3 | 0.7 | Noise/invalid region[cite: 2] | `INVALID / NOISE REGION` |
| 3.4 | 1.4 | 2.0 | Dominant[cite: 2] | `DOMINANT` |

---

## Sample Console Output

```text
===================================================
   Activity 2 - High-Speed CAN Voltage Monitor     
===================================================

Enter Bus Bit Rate (kbps): 500
Enter CAN_H voltage (V): 3.5
Enter CAN_L voltage (V): 1.5

---------------------------------------------------
                  MONITOR OUTPUT                   
---------------------------------------------------
CAN_H = 3.50 V
CAN_L = 1.50 V
Vdiff = 2.00 V

CAN BUS STATE : DOMINANT
---------------------------------------------------