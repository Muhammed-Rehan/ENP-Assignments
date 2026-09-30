#include <stdio.h>
#include <stdbool.h>

// Structure to define medium characteristics
typedef struct {
    const char* name;
    int num_wires;
    const char* noise_rejection;
    const char* radiation_susceptibility;
    const char* recommended_app;
} CAN_Medium_Props;

// Static lookup table for CAN Physical Media characteristics
const CAN_Medium_Props media_table[3] = {
    {
        .name = "Single-wire CAN",
        .num_wires = 1,
        .noise_rejection = "LOW",
        .radiation_susceptibility = "HIGH",
        .recommended_app = "Low-speed body electronics, comfort control"
    },
    {
        .name = "Differential Twisted-Pair CAN",
        .num_wires = 2,
        .noise_rejection = "HIGH",
        .radiation_susceptibility = "LOW",
        .recommended_app = "Powertrain, chassis control, high-speed automotive networks"
    },
    {
        .name = "Twisted-Pair with Screen",
        .num_wires = 3, // 2 signal wires + 1 shielding/screen
        .noise_rejection = "VERY HIGH",
        .radiation_susceptibility = "VERY LOW",
        .recommended_app = "Industrial automation, harsh EMI environments"
    }
};

// Function prototypes
void display_medium_properties(int medium_type);
bool check_suitability(int medium_type, int bit_rate, float bus_length, int fault_type, int termination);
void compare_alternatives(int selected_medium);

int main(void) {
    int media_type, bit_rate, node_count, fault_type, termination, noise_level;
    float bus_length;

    printf("===================================================\n");
    printf("   Activity 4.1 - CAN Physical Media Evaluation\n");
    printf("===================================================\n\n");

    // 1. Select CAN medium
    printf("Select CAN Medium:\n");
    printf("  1 = Single-wire CAN\n");
    printf("  2 = Differential Twisted-Pair CAN\n");
    printf("  3 = Twisted-Pair with Screen\n");
    printf("Enter choice (1-3): ");
    scanf("%d", &media_type);

    if (media_type < 1 || media_type > 3) {
        printf("Invalid medium selected!\n");
        return 1;
    }

    // 2. Enter bit rate, length, and number of nodes
    printf("\nEnter Bit Rate (125, 250, 500, 1000 kbps): ");
    scanf("%d", &bit_rate);

    printf("Enter Bus Length (in metres): ");
    scanf("%f", &bus_length);

    printf("Enter Number of CAN Nodes: ");
    scanf("%d", &node_count);

    // 3. Select fault condition and other parameters
    printf("\nSelect Fault Type (0 = No fault, 1 = Open, 2 = Short): ");
    scanf("%d", &fault_type);

    printf("Enter Noise Level (0 - 100%%): ");
    scanf("%d", &noise_level);

    printf("Enter Termination (0 = Absent, 1 = Present): ");
    scanf("%d", &termination);

    printf("\n---------------------------------------------------\n");
    printf("                 EVALUATION REPORT                 \n");
    printf("---------------------------------------------------\n");

    // Display selected media details
    const CAN_Medium_Props selected = media_table[media_type - 1];
    printf("CAN Medium        : %s\n", selected.name);
    printf("Wires             : %d\n", selected.num_wires);
    printf("Noise Rejection   : %s\n", selected.noise_rejection);
    printf("Radiation         : %s\n", selected.radiation_susceptibility);
    printf("Bit Rate          : %d kbps\n", bit_rate);
    printf("Bus Length        : %.0f m\n", bus_length);
    printf("Nodes             : %d\n", node_count);
    printf("Termination       : %s\n", (termination == 1) ? "OK" : "MISSING");

    // Display fault effect if any
    printf("Fault Effect      : ");
    if (fault_type == 1) {
        printf("Bus line OPEN circuit - Signal degradation/loss\n");
    } else if (fault_type == 2) {
        printf("Bus line SHORT circuit - Total communication failure\n");
    } else {
        printf("None\n");
    }

    printf("Recommended App   : %s\n", selected.recommended_app);

    // Evaluate physical medium suitability
    bool is_suitable = check_suitability(media_type, bit_rate, bus_length, fault_type, termination);
    printf("Bus Status        : %s\n", is_suitable ? "SUITABLE" : "UNSUITABLE");

    // Extension Task: Compare with alternative physical media
    printf("\n===================================================\n");
    printf("       EXTENSION: COMPARISON WITH ALTERNATIVES     \n");
    printf("===================================================\n");
    compare_alternatives(media_type);

    return 0;
}

// Function to evaluate whether the configured setup is suitable
bool check_suitability(int medium_type, int bit_rate, float bus_length, int fault_type, int termination) {
    // Basic validation rule set:
    // 1. Fault presence invalidates bus functionality
    if (fault_type != 0) return false;

    // 2. High-speed CAN requires proper termination resistors
    if (termination == 0) return false;

    // 3. Single-wire CAN constraints (typically max 33.3 kbps to 100 kbps max)
    if (medium_type == 1 && bit_rate > 100) return false;

    // 4. Standard ISO 11898 length vs speed limitations
    if (bit_rate == 1000 && bus_length > 40) return false;
    if (bit_rate == 500 && bus_length > 100) return false;
    if (bit_rate == 250 && bus_length > 250) return false;
    if (bit_rate == 125 && bus_length > 500) return false;

    return true;
}

// Function for extension task to compare media alternatives
void compare_alternatives(int selected_medium) {
    for (int i = 0; i < 3; i++) {
        printf("\n[%s] %s\n", 
               (i + 1 == selected_medium) ? "SELECTED" : "ALTERNATIVE", 
               media_table[i].name);
        printf("  - Wires: %d\n", media_table[i].num_wires);
        printf("  - Noise Rejection: %s\n", media_table[i].noise_rejection);
        printf("  - Radiation Susceptibility: %s\n", media_table[i].radiation_susceptibility);
        printf("  - Recommended Use: %s\n", media_table[i].recommended_app);
    }
}