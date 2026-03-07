from scapy.all import *

def detect_dhcp_servers():
    # get local mac address
    local_mac = get_if_hwaddr(conf.iface)
    # Send a DHCP Discover packet to detect DHCP servers

    dhcp_discover = (
        Ether(src=local_mac ,dst="ff:ff:ff:ff:ff:ff") / 
        IP(dst="255.255.255.255") / UDP(sport=68, dport=67) / 
        BOOTP(op=1, chaddr=local_mac) / 
        DHCP(options=[("message-type", "discover"), "end"]))
    
    sendp(dhcp_discover, iface=conf.iface)
    

# callback function to process DHCP Offer responses
def offer_callback(pkt):
    if DHCP:
        for option in pkt[DHCP].options:
            if option[0] == "message-type" and option[1] == 2:
                print(f"DHCP Offer from {pkt[Ether].src} ({pkt[IP].src})")

if __name__ == "__main__":
    detect_dhcp_servers()
    # Sniff for DHCP Offer responses
    sniff(filter="udp and (port 67 or 68)", prn=offer_callback)
