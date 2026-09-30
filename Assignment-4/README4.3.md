# 8-Node CAN Bus Transmission & ACK/NACK Simulation

This project presents an Embedded C simulation of a Controller Area Network (CAN) bus consisting of 8 nodes. It demonstrates broadcast transmission, acceptance filtering, and the CAN physical layer's Wired-AND Acknowledgement (ACK/NACK) mechanism.

---

## Bus Scenario Overview

1. **Transmitter**: Node 1 broadcasts a CAN frame with target ID `8`.
2. **Receivers**: Nodes 2 through 8 monitor the bus broadcast simultaneously.
3. **Filtering**:
   * **Nodes 2–7**: Detect an ID mismatch, reject the message, and send a **Negative ACK (NACK / Recessive `1`)**.
   * **Node 8**: Detects an ID match, accepts the message, and drives the **Positive ACK (Dominant `0`)**.
4. **Wired-AND Result**: Because CAN lines act as a Wired-AND network, the single Dominant (`0`) driven by Node 8 pulls the ACK slot low, confirming successful delivery to Node 1.

---

## Structural Overview

### CAN Frame Structure
```c
typedef struct {
    uint32_t id;         // Identifier (Target ID)
    uint8_t dlc;         // Data Length Code
    uint8_t data[8];     // Payload array
    bool ack_bit;        // Bus ACK slot (0 = Dominant/ACK, 1 = Recessive/NACK)
} CAN_Frame;
```

### CAN Node Structure
```c
typedef struct {
    uint8_t node_id;     // Node ID
    uint32_t filter_id;  // Hardware acceptance filter
} CAN_Node;
```

---

## Simulated Execution Output

```text
=====================================================
        CAN BUS 8-NODE ACK/NACK SIMULATION           
=====================================================

[TX] Node 1 Broadcasting Frame...
     Target ID : 8
     DLC       : 4
     Data      : 0xDE 0xAD 0xBE 0xEF

-----------------------------------------------------
               BUS RECEPTION & FILTERING             
-----------------------------------------------------
Node 2: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 3: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 4: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 5: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 6: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 7: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)
Node 8: ID Match (0x08) -> ACCEPTED  | Sending POSITIVE ACK (Dominant 0)

-----------------------------------------------------
                    FINAL BUS STATUS                 
-----------------------------------------------------
ACK Slot Result: DOMINANT (0) -> Frame Transmission SUCCESSFUL
-----------------------------------------------------
```

---

## Compilation & Execution

To compile and run the simulation using `gcc`:

```bash
gcc assignment4.3.c
./a.out
```