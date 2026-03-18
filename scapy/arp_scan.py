from scapy.all import *
import argparse
from ipaddress import ip_network

def arp_scan(target_subnet):
    # construct arp request packet
    registred_clients = {}
    ip_list = [str(ip) for ip in ip_network(target_subnet).hosts()]
    arp_reqs = [Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1,pdst=target_ip) for target_ip in ip_list]
    # send the arp request packet and receive response
    msg = srp(arp_reqs, timeout=2, verbose=False)
    # process the response
    for sent, received in msg[0]:
        if(received):
            registred_clients[received.psrc] = received.hwsrc
    return registred_clients

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARP Scanner")
    parser.add_argument("target_subnet", help="Target subnet (e.g.,192.168.1.0/24)")
    args = parser.parse_args()
    clients = arp_scan(args.target_subnet)

    print("IP Address\t\tMAC Address")
    print("-----------------------------------------")
    for ip, mac in clients.items():
        print(f"{ip}\t\t{mac}")
