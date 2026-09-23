# CAN Bus Node Error State Simulator

This project is a lightweight C program that simulates the error management and node state transitions defined in the **Controller Area Network (CAN)** protocol standard. It tracks Transmission Error Counters (TEC) and Reception Error Counters (REC) to determine whether a node is in an **Error Active**, **Error Passive**, or **Bus Off** state.

## Features

- **Error Counter Tracking:** Manages increments and decrements for both transmission and reception errors based on standard CAN behavior heuristics.
- **State Machine Logic:** Dynamically evaluates node states according to standard thresholds:
  - **Error Active:** $\text{TEC} \le 127$ and $\text{REC} \le 127$
  - **Error Passive:** $\text{TEC} > 127$ or $\text{REC} > 127$ (and $\text{TEC} \le 255$)
  - **Bus Off:** $\text{TEC} > 255$
- **Boundary Protection:** Prevents error counters from dropping below zero.
- **Demonstration Script:** Includes a `main` function showing step-by-step state transitions under various error and success conditions.

---

## Code Overview

### Global Variables
- `static int TEC`: Transmit Error Counter (default initialized to 0).
- `static int REC`: Receive Error Counter (default initialized to 0).

### Core Functions
- `void transmission_error(int num)`: Increases TEC by $8 \times \text{num}$.
- `void reception_error(int num)`: Increases REC by $1 \times \text{num}$.
- `void transmission_success(int num)`: Decreases TEC by $1 \times \text{num}$ (floored at 0).
- `void reception_success(int num)`: Decreases REC by $1 \times \text{num}$ (floored at 0).
- `void update_node_state(char *state)`: Evaluates current TEC and REC values to update the node status string.

---

## Getting Started

### Prerequisites
You need a standard C compiler (such as `gcc`, `clang`, or MSVC) installed on your system.

### Compilation & Execution

1. Save the code into a file named `can_simulator.c`.
2. Open your terminal or command prompt and compile the program:
   ```bash
   gcc can_simulator.c -o can_simulator
   ```
3. Run the executable:
   ```bash
   ./can_simulator
   ```

---

## Example Output

When executed, the program runs through 5 predefined simulation steps, displaying counter values and state changes:

```text
step:1 TEC: 0 and REC: 0, State: ERROR ACTIVE
step:2 TEC: 80 and REC: 0, State: ERROR ACTIVE
step:3 TEC: 74 and REC: 0, State: ERROR ACTIVE
step:4 TEC: 64 and REC: 0, State: ERROR ACTIVE
step:5 transmission overload TEC: 224 and REC: 0, State: ERROR PASSIVE