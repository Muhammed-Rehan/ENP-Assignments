#include <stdio.h>
#include <stdbool.h>

// CAN Node States
typedef enum {
    ERROR_ACTIVE,
    ERROR_PASSIVE,
    BUS_OFF
} CAN_NodeState;

// CAN Node Structure
typedef struct {
    int TEC;
    int REC;
    CAN_NodeState state;
} CAN_Node;

// Function to update state based on CAN spec thresholds
void update_node_state(CAN_Node *node) {
    if (node->TEC > 255) {
        node->state = BUS_OFF;
    } else if (node->TEC > 127 || node->REC > 127) {
        node->state = ERROR_PASSIVE;
    } else {
        node->state = ERROR_ACTIVE;
    }
}

// Helper to print current state string
const char* get_state_string(CAN_NodeState state) {
    switch (state) {
        case ERROR_ACTIVE:  return "ERROR ACTIVE";
        case ERROR_PASSIVE: return "ERROR PASSIVE";
        case BUS_OFF:       return "BUS OFF";
        default:            return "UNKNOWN";
    }
}

// Display current status
void print_status(const CAN_Node *node) {
    printf("TEC: %3d | REC: %3d | State: %s\n", 
           node->TEC, node->REC, get_state_string(node->state));
}

// Event Simulators
void on_tx_success(CAN_Node *node) {
    if (node->state == BUS_OFF) return;
    if (node->TEC > 0) node->TEC--;
    update_node_state(node);
}

void on_tx_error(CAN_Node *node) {
    if (node->state == BUS_OFF) return;
    node->TEC += 8;
    update_node_state(node);
}

void on_rx_error(CAN_Node *node) {
    if (node->state == BUS_OFF) return;
    node->REC += 1;
    update_node_state(node);
}

int main(void) {
    CAN_Node node = { .TEC = 0, .REC = 0, .state = ERROR_ACTIVE };

    printf("--- CAN Fault Confinement Simulation ---\n");
    print_status(&node);

    printf("\n1. Simulating 16 consecutive Transmission Errors (+8 TEC each)...\n");
    for (int i = 0; i < 16; i++) {
        on_tx_error(&node);
    }
    print_status(&node);

    printf("\n2. Simulating 10 Successful Transmissions (-1 TEC each)...\n");
    for (int i = 0; i < 10; i++) {
        on_tx_success(&node);
    }
    print_status(&node);

    printf("\n3. Simulating non-stop Transmission Errors to force BUS OFF...\n");
    while (node.state != BUS_OFF) {
        on_tx_error(&node);
    }
    print_status(&node);

    printf("\n4. Attempting TX on BUS OFF node (Ignored)...\n");
    on_tx_success(&node);
    print_status(&node);

    return 0;
}