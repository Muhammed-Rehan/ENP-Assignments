class CAN20ANode:
    def __init__(self, name: str, can_id: int, data_bytes: list[int]):
        """
        CAN 2.0A Node Initializer.
        :param name: Node label (e.g., 'ECU_Engine')
        :param can_id: 11-bit Identifier (0 to 2047)
        :param data_bytes: List of integers (0-255), max 8 bytes
        """
        if can_id > 0x7FF or can_id < 0:
            raise ValueError("CAN 2.0A supports 11-bit identifiers only (0x000 to 0x7FF).")
        if len(data_bytes) > 8:
            raise ValueError("CAN Data field cannot exceed 8 bytes.")

        self.name = name
        self.can_id = can_id
        self.data_bytes = data_bytes
        self.state = "TRANSMITTING"  # TRANSMITTING, LOST_ARBITRATION, COMPLETED
        self.raw_frame = self._build_can_20a_frame()

    def _calculate_crc15(self, bit_string: str) -> str:
        """Calculates standard CAN 15-bit CRC using polynomial x^15 + x^14 + x^10 + x^8 + x^7 + x^4 + x^3 + 1."""
        crc = 0x0000
        for bit in bit_string:
            b = int(bit)
            crc_nxt = b ^ ((crc >> 14) & 1)
            crc = (crc << 1) & 0x7FFF
            if crc_nxt:
                crc ^= 0x4599
        return f"{crc:015b}"

    def _build_can_20a_frame(self) -> str:
        # 1. SOF: 1 bit (0)
        sof = "0"
        
        # 2. Arbitration Field: 11-bit ID + RTR bit (0 for data frame)
        arb = f"{self.can_id:011b}" + "0"
        
        # 3. Control Field: IDE (0 for CAN 2.0A) + r0 (0) + DLC (4 bits)
        dlc = f"{len(self.data_bytes):04b}"
        ctrl = "0" + "0" + dlc
        
        # 4. Data Field: Payload bytes converted to binary
        data = "".join(f"{b:08b}" for b in self.data_bytes)
        
        # Unstuffed bits up to CRC calculation
        header_and_data = sof + arb + ctrl + data
        
        # 5. CRC Field: 15-bit CRC + CRC Delimiter (1)
        crc_val = self._calculate_crc15(header_and_data)
        crc_field = crc_val + "1"
        
        # 6. ACK Field: ACK Slot (1) + ACK Delimiter (1)
        ack_field = "11"
        
        # 7. EOF: 7 Recessive bits (1111111)
        eof = "1111111"
        
        return header_and_data + crc_field + ack_field + eof


def apply_bit_stuffing(bit_stream: str) -> str:
    """
    Applies Bit Stuffing: Inserts an inverted bit after 5 consecutive identical bits.
    Note: Bit stuffing applies from SOF through the CRC field (excludes CRC Delimiter, ACK, and EOF).
    """
    # Exclude ACK and EOF from stuffing per spec
    stuffable_len = len(bit_stream) - 10 
    stuffable_part = bit_stream[:stuffable_len]
    fixed_part = bit_stream[stuffable_len:]

    stuffed = ""
    consecutive = 1
    last_bit = None

    for bit in stuffable_part:
        if bit == last_bit:
            consecutive += 1
        else:
            consecutive = 1
            last_bit = bit

        stuffed += bit

        if consecutive == 5:
            stuffed_bit = '0' if bit == '1' else '1'
            stuffed += f"[{stuffed_bit}]"  # Bracketed for visual clarity in logs
            consecutive = 1
            last_bit = stuffed_bit

    return stuffed + fixed_part


def run_simulation(nodes: list[CAN20ANode]):
    print("=========================================================================")
    print("                    CAN 2.0A PROTOCOL SIMULATION                         ")
    print("=========================================================================\n")

    stuffed_streams = [apply_bit_stuffing(n.raw_frame) for n in nodes]

    for i, node in enumerate(nodes):
        print(f"Node: {node.name:<15} | ID: 0x{node.can_id:03X} ({node.can_id:011b}) | Payload: {node.data_bytes}")
        print(f"Frame Stream: {stuffed_streams[i]}\n")

    print("-" * 75)
    print(f"{'Clock':<6} | {'Bus State':<11} | " + " | ".join([f"{n.name[:8]:<8}" for n in nodes]) + " | Event")
    print("-" * 75)

    max_clock = max(len(s) for s in stuffed_streams)
    pointers = [0] * len(nodes)

    for clock in range(max_clock):
        current_bits = []

        # Determine bit sent by each node
        for i, node in enumerate(nodes):
            stream = stuffed_streams[i]
            ptr = pointers[i]

            if node.state == "TRANSMITTING" and ptr < len(stream):
                # Skip bracket characters used for formatting stuffed bits
                if stream[ptr] in "[]":
                    pointers[i] += 1
                    ptr = pointers[i]
                bit = stream[ptr]
            else:
                bit = '1'  # Idle/Lost nodes remain Recessive

            current_bits.append(bit)

        # Wired-AND Logic: Any '0' (Dominant) drives the bus to '0'
        bus_state = '0' if '0' in current_bits else '1'

        # Check Arbitration
        events = []
        for i, node in enumerate(nodes):
            if node.state == "TRANSMITTING" and pointers[i] < len(stuffed_streams[i]):
                bit_sent = current_bits[i]
                if bit_sent == '1' and bus_state == '0':
                    node.state = "LOST_ARBITRATION"
                    events.append(f"{node.name} lost arbitration")

        # Formatting Output
        bit_displays = []
        for i, node in enumerate(nodes):
            if node.state == "LOST_ARBITRATION":
                bit_displays.append(f"{'OFF':<8}")
            else:
                bit_displays.append(f"{current_bits[i]:<8}")

        event_str = ", ".join(events) if events else ""
        bus_str = "0 (DOM)" if bus_state == '0' else "1 (REC)"
        print(f"{clock:<6d} | {bus_str:<11} | " + " | ".join(bit_displays) + f" | {event_str}")
        # Advance pointer for active nodes
        for i in range(len(nodes)):
            if pointers[i] < len(stuffed_streams[i]):
                pointers[i] += 1

    print("-" * 75)
    print("Transmission complete.\n")


# --- RUN TEST CASE ---
if __name__ == "__main__":
    # Node 1: ID 0x120 (00100100000)
    # Node 2: ID 0x0FE (00011111110) --> Lower numerical ID wins arbitration early
    ecu1 = CAN20ANode(name="Brake_ECU", can_id=0x120, data_bytes=[0xAB, 0xCD])
    ecu2 = CAN20ANode(name="Engine_ECU", can_id=0x0FE, data_bytes=[0x12])

    run_simulation([ecu1, ecu2])