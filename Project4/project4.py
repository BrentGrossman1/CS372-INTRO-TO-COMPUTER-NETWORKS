# Project 4: Validating a TCP Packet
# Checks each TCP data file against its IP addresses by recomputing
# the TCP checksum.  Prints PASS if it matches, FAIL if the data is corrupted.


# Converts an IP address string like "1.2.3.4" into 4 bytes: b'\x01\x02\x03\x04'
def ip_to_bytes(ip_address):

    ip_bytes = b""

    # Each number between the dots becomes 1 byte
    for number in ip_address.split("."):
        ip_octet = int(number)
        ip_bytes += bytes([ip_octet])

    return ip_bytes


# Computes the TCP checksum (one's complement sum of all 16-bit words)
# Data must be an even number of bytes
def compute_checksum(data):
    total = 0

    # walk through the data 2 bytes (16 bits) at a time
    for i in range(0, len(data), 2):
        word = int.from_bytes(data[i:i+2], "big")
        total += word

        # Carry around: wrap any overflow past 16 bits back to the bottom
        total = (total & 0xffff) + (total >> 16)

    # Flip all the bits and keep it to 16 bits
    return (~total) & 0xffff


# Check all 10 test files 
for i in range(10):

    # Read the source and destination IP addresses
    with open(f"tcp_data/tcp_addrs_{i}.txt") as addresses_file:
        source_ip, dest_ip = addresses_file.read().split()

    source_bytes = ip_to_bytes(source_ip)
    dest_bytes = ip_to_bytes(dest_ip)

    # Read the TCP header and payload.  "rb" = read as bytes, not text
    with open(f"tcp_data/tcp_data_{i}.dat", "rb") as data_file:
        tcp_data = data_file.read()

    # Length of the TCP data before any padding, needed for the pseudo header
    tcp_length = len(tcp_data)

    # Build the IP pseudo header, 12 bytes, not actually sent
    # Layout: source IP (4) + dest IP (4) + zero (1) + protocol (1) + TCP length (2)
    # It ties the IP addresses into the checksum
    zero_byte = b'\x00'
    tcp_protocol = b'\x06'  # 6 is IP's protocol number for TCP
    length_bytes = tcp_length.to_bytes(2, "big")
    pseudo_header = source_bytes + dest_bytes + zero_byte + tcp_protocol + length_bytes

    # The checksum the sender put in the packet, bytes 16-17 of the TCP header
    original_checksum = int.from_bytes(tcp_data[16:18], "big")

    # Copy of the TCP data with the checksum spot set to zero
    # The checksum is always computed with this field zeroed
    tcp_zero_checksum = tcp_data[:16] + b'\x00\x00' + tcp_data[18:]

    # Pad with a zero byte if the length is odd, since the checksum works on 2-byte chunks
    if len(tcp_zero_checksum) % 2 == 1:
        tcp_zero_checksum += b'\x00'

    # Compute our own checksum over pseudo header + zeroed TCP data
    data_to_check = pseudo_header + tcp_zero_checksum
    computed_checksum = compute_checksum(data_to_check)

    # Matching checksums means data is intact, otherwise it's corrupted
    if computed_checksum == original_checksum:
        print("PASS")
    else:
        print("FAIL")