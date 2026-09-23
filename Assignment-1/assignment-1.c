#include <stdio.h>
#include <string.h>

// Functions declared outside main (Standard C syntax)
static int TEC = 0;
static int REC = 0;

void transmission_error(int num) {
    TEC = TEC + num * 8;
}

void reception_error(int num) {
    REC = REC + num * 1;
}

void transmission_success(int num) {
    TEC = TEC - num * 1;
    if (TEC < 0) TEC = 0; // Prevent negative error counts
}

void reception_success(int num) {
    REC = REC - num * 1;
    if (REC < 0) REC = 0; // Prevent negative error counts
}

void update_node_state(char *state) {
    if (TEC > 255) {
        strcpy(state, "BUS OFF");
    } else if (TEC > 127 || REC > 127) {
        strcpy(state, "ERROR PASSIVE");
    } else {
        strcpy(state, "ERROR ACTIVE");
    }
}

int main() {
    char CAN_nodestate[20] = "";

    update_node_state(CAN_nodestate);
    printf("step:1 TEC: %d and REC: %d, State: %s\n", TEC, REC, CAN_nodestate);

    printf("step:2 ");
    transmission_error(10);
    update_node_state(CAN_nodestate);
    printf("TEC: %d and REC: %d, State: %s\n", TEC, REC, CAN_nodestate);

    printf("step:3 ");
    transmission_success(6);
    update_node_state(CAN_nodestate);
    printf("TEC: %d and REC: %d, State: %s\n", TEC, REC, CAN_nodestate);

    printf("step:4 ");
    transmission_success(10);
    update_node_state(CAN_nodestate);
    printf("TEC: %d and REC: %d, State: %s\n", TEC, REC, CAN_nodestate);

    printf("step:5 ");
    transmission_error(20);
    printf("transmission overload ");
    update_node_state(CAN_nodestate);
    printf("TEC: %d and REC: %d, State: %s\n", TEC, REC, CAN_nodestate);

    return 0;
}