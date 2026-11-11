#include <stdio.h>
#include <math.h>

// Coding Parameters (as specified in problem statement)
#define RECESSIVE_THRESHOLD 0.5f
#define DOMINANT_THRESHOLD  0.9f

#define CAN_H_RECESSIVE     2.5f
#define CAN_L_RECESSIVE     2.5f

#define CAN_H_DOMINANT      3.5f
#define CAN_L_DOMINANT      1.5f

// Enum for CAN bus states
typedef enum {
    STATE_RECESSIVE,
    STATE_DOMINANT,
    STATE_INVALID_NOISE,
    STATE_BOUNDARY
} CAN_BusState;

// Function prototype
CAN_BusState evaluate_can_state(float vdiff);
const char* get_state_string(CAN_BusState state);

int main(void) {
    float can_h, can_l, vdiff;
    int bit_rate;

    printf("===================================================\n");
    printf("   Activity 2 - High-Speed CAN Voltage Monitor     \n");
    printf("===================================================\n\n");

    // Inputs
    printf("Enter Bus Bit Rate (kbps): ");
    if (scanf("%d", &bit_rate) != 1) {
        printf("Invalid input for bit rate.\n");
        return 1;
    }

    printf("Enter CAN_H voltage (V): ");
    if (scanf("%f", &can_h) != 1) {
        printf("Invalid input for CAN_H.\n");
        return 1;
    }

    printf("Enter CAN_L voltage (V): ");
    if (scanf("%f", &can_l) != 1) {
        printf("Invalid input for CAN_L.\n");
        return 1;
    }

    // Required Calculation: Vdiff = CAN_H - CAN_L
    vdiff = can_h - can_l;

    // Evaluate state
    CAN_BusState bus_state = evaluate_can_state(vdiff);

    // Display Output matching expected format
    printf("\n---------------------------------------------------\n");
    printf("                  MONITOR OUTPUT                   \n");
    printf("---------------------------------------------------\n");
    printf("CAN_H = %.2f V\n", can_h);
    printf("CAN_L = %.2f V\n", can_l);
    printf("Vdiff = %.2f V\n\n", vdiff);
    printf("CAN BUS STATE : %s\n", get_state_string(bus_state));
    printf("---------------------------------------------------\n");

    return 0;
}

// Logic Function
CAN_BusState evaluate_can_state(float vdiff) {
    // Handle floating-point exact boundary check (0.5V boundary)
    if (fabsf(vdiff - RECESSIVE_THRESHOLD) < 0.001f) {
        return STATE_BOUNDARY;
    }
    
    if (vdiff < RECESSIVE_THRESHOLD) {
        return STATE_RECESSIVE;
    } else if (vdiff > DOMINANT_THRESHOLD) {
        return STATE_DOMINANT;
    } else {
        return STATE_INVALID_NOISE;
    }
}

// Utility function to convert enum to text display
const char* get_state_string(CAN_BusState state) {
    switch (state) {
        case STATE_RECESSIVE:     return "RECESSIVE";
        case STATE_DOMINANT:      return "DOMINANT";
        case STATE_BOUNDARY:      return "Boundary (Transition Region)";
        case STATE_INVALID_NOISE: return "INVALID / NOISE REGION";
        default:                  return "UNKNOWN";
    }
}