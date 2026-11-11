#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#define TOTAL_NODES 8
#define TARGET_NODE_ID 8

// Structure representing a CAN Frame
typedef struct {
    uint32_t id;         // CAN Identifier (Target Node ID in this logic)
    uint8_t dlc;         // Data Length Code
    uint8_t data[8];     // Data payload
    bool ack_bit;        // Recessive (true = ACK Error) / Dominant (false = ACK Success)
} CAN_Frame;

// Structure representing a CAN Node
typedef struct {
    uint8_t node_id;
    uint32_t filter_id;  // Accepted CAN ID
} CAN_Node;

// Function prototypes
void can_bus_transmit(CAN_Node nodes[], CAN_Frame *frame, uint8_t transmitter_id);

int main(void) {
    // 1. Initialize 8 CAN Nodes
    CAN_Node nodes[TOTAL_NODES];
    for (int i = 0; i < TOTAL_NODES; i++) {
        nodes[i].node_id = i + 1;
        nodes[i].filter_id = i + 1; // Node accepts messages matching its Node ID
    }

    // 2. Prepare CAN Frame from Node 1 intended for Node 8
    CAN_Frame frame = {
        .id = TARGET_NODE_ID,
        .dlc = 4,
        .data = {0xDE, 0xAD, 0xBE, 0xEF},
        .ack_bit = true // Transmitted as Recessive (1) by Sender
    };

    printf("=====================================================\n");
    printf("        CAN BUS 8-NODE ACK/NACK SIMULATION           \n");
    printf("=====================================================\n\n");

    printf("[TX] Node 1 Broadcasting Frame...\n");
    printf("     Target ID : %u\n", frame.id);
    printf("     DLC       : %u\n", frame.dlc);
    printf("     Data      : 0x%02X 0x%02X 0x%02X 0x%02X\n\n", 
           frame.data[0], frame.data[1], frame.data[2], frame.data[3]);

    // 3. Transmit frame over the bus
    can_bus_transmit(nodes, &frame, 1);

    return 0;
}

void can_bus_transmit(CAN_Node nodes[], CAN_Frame *frame, uint8_t transmitter_id) {
    bool bus_ack_line = true; // Recessive state (No ACK)

    printf("-----------------------------------------------------\n");
    printf("               BUS RECEPTION & FILTERING             \n");
    printf("-----------------------------------------------------\n");

    for (int i = 0; i < TOTAL_NODES; i++) {
        uint8_t current_id = nodes[i].node_id;

        // Hardware Acceptance Filter Check
        if (nodes[i].filter_id == frame->id) {
            // Target Node matches message ID -> Accept & Drive ACK Dominant (0)
            printf("Node %d: ID Match (0x%02X) -> ACCEPTED  | Sending POSITIVE ACK (Dominant 0)\n", 
                   current_id, frame->id);
            bus_ack_line = false; // Driving bus to Dominant state (0)
        } else {
            // Non-target Node -> Reject ID & Send NACK (Recessive 1)
            printf("Node %d: ID Mismatch        -> IGNORED   | Sending NEGATIVE ACK (Recessive 1)\n", 
                   current_id);
        }
    }

    // Update frame's final ACK status on the bus
    frame->ack_bit = bus_ack_line;

    printf("\n-----------------------------------------------------\n");
    printf("                    FINAL BUS STATUS                 \n");
    printf("-----------------------------------------------------\n");
    if (frame->ack_bit == false) {
        printf("ACK Slot Result: DOMINANT (0) -> Frame Transmission SUCCESSFUL\n");
    } else {
        printf("ACK Slot Result: RECESSIVE (1) -> ACK ERROR (NACK)\n");
    }
    printf("-----------------------------------------------------\n");
}