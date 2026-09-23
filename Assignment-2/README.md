# CAN 2.0A (Standard CAN) Bit-Level Protocol Simulator

This repository contains a Python implementation designed to simulate the bit-level operations of the **Controller Area Network (CAN) 2.0A** protocol. It demonstrates frame construction, bit stuffing, CRC generation, bus arbitration (Wired-AND logic), and state tracking across transmitting nodes.

---

## 1. How the CAN 2.0A Protocol Works

CAN is a multi-master, broadcast, serial bus standard. It communicates without a central host using differential physical signaling over two wires (CAN High and CAN Low).

### Key Rules Represented in Code
1. **Wired-AND Logic (Dominant vs. Recessive):**
   - **`0` (Dominant):** Driven actively by nodes. If any node transmits `0`, the bus state becomes `0`.
   - **`1` (Recessive):** Passive state. The bus remains `1` only if all transmitting nodes send `1`.
2. **Bit-Wise Non-Destructive Arbitration:**
   - Nodes begin transmitting their 11-bit Identifiers simultaneously.
   - Every node monitors the actual state of the bus while sending.
   - If a node transmits a Recessive bit (`1`) but senses a Dominant bit (`0`) on the bus, it immediately loses arbitration and stops transmitting.
   - The node with the **lower numerical CAN ID** has higher priority and wins the bus without frame corruption.
3. **Bit Stuffing:**
   - After **5 consecutive identical bits** (0s or 1s), the transmitting hardware automatically inserts 1 opposite bit to maintain receiver clock synchronization.
   - Bracket notation (e.g., `[0]` or `[1]`) is used in the simulation log to denote stuffed bits.

---

## 2. CAN 2.0A Frame Structure

The Python code builds the exact frame structure specified in standard CAN 2.0A:

| Field Name | Bit Width | Purpose |
| :--- | :--- | :--- |
| **SOF** | 1 bit | Start of Frame (always `0`). |
| **Arbitration** | 12 bits | 11-bit CAN ID + 1 RTR bit (`0` for Data Frame). |
| **Control** | 6 bits | IDE bit (`0` for 2.0A) + r0 (Reserved `0`) + 4 DLC bits (data byte count). |
| **Data** | 0 to 64 bits | Binary representation of payload bytes (0 to 8 bytes). |
| **CRC** | 16 bits | 15-bit calculated CRC polynomial + 1 CRC Delimiter (`1`). |
| **ACK** | 2 bits | 1 ACK Slot (`1`, overwritten by receivers) + 1 ACK Delimiter (`1`). |
| **EOF** | 7 bits | End of Frame (`1111111`). |

---

## 3. Code Architecture Overview

### Classes & Functions

1. **`CAN20ANode` Class:**
   - Encapsulates node properties (ID, name, payload).
   - `_build_can_20a_frame()`: Assembles the raw bit string based on standard CAN 2.0A fields.
   - `_calculate_crc15()`: Performs polynomial long division using the official CAN CRC-15 polynomial ($x^{15} + x^{14} + x^{10} + x^8 + x^7 + x^4 + x^3 + 1$).

2. **`apply_bit_stuffing(bit_stream)`:**
   - Evaluates the bit stream from SOF through the CRC field.
   - Dynamically inserts opposite stuffed bits whenever 5 consecutive identical bits appear.

3. **`run_simulation(nodes)`:**
   - Simulates the hardware clock cycles.
   - Implements **Wired-AND** logic across all active nodes (`bus_state = '0' if '0' in current_bits else '1'`).
   - Handles bit monitoring: flags nodes that lose arbitration and drops them to passive mode (`OFF`).

---

## 4. Example Output Walkthrough

When `Brake_ECU` (ID: `0x120` / `00100100000`) and `Engine_ECU` (ID: `0x0FE` / `00011111110`) transmit simultaneously:

```text
Clock  | Bus State   | Brake_EC | Engine_E | Event
---------------------------------------------------------------------------
000    | 0 (DOM)     | 0        | 0        | 
001    | 0 (DOM)     | 0        | 0        | 
002    | 0 (DOM)     | 1        | 0        | --> Brake_ECU lost arbitration
003    | 0 (DOM)     | OFF      | 0        |