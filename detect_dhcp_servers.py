from scapy.all import *


# Preparing DCHP Discovery Message

msg = (Ether(dst="ff:ff:ff:ff:ff:ff")
        /IP(dst="255.255.255.255")
        /UDP(sport=68, dport=67)
        /BOOTP(chaddr=get_if_hwaddr(conf.iface)) # get_if_hwaddr() is used to get the MAC address of the interface
        /DHCP(options=[("message-type", "discover"), "end"])
)
# sending the message to the network to detect any rouge DHCP servers
sendp(msg, iface=conf.iface)

# Callback function to process incoming DHCP Offer messages
def dhcp_monitor_callback(pkt):
    if DHCP in pkt and pkt[DHCP].options[0][1] == 2: # DHCP Offer
        print(f"DHCP Server Detected {pkt[IP].src} with MAC {pkt[Ether].src}")
# Sniffing for DHCP Offer messages on the network
sniff(prn=dhcp_monitor_callback, filter="udp and (port 67 or 68)", store=0)
