#!/usr/bin/env python3
"""
LEVEL 6: gNMI Basics - Get Operations for Telemetry Data
==========================================================
Topics covered:
  - gNMI client setup with pygnmi
  - Capabilities discovery (gNMI-specific, different from NETCONF)
  - Get operations on OpenConfig paths
  - Understanding gNMI notification structure (timestamp, update, path, val)
  - Parsing structured protobuf/gRPC responses as Python dicts
  - Comparing gNMI vs NETCONF for data retrieval
"""
import socket
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])
target = (ip, str(cfg["gnmi_port"]))

print("=" * 60)
print("LEVEL 6: gNMI Get Operations")
print("=" * 60)
print(f"Device: {cfg['hostname']} ({ip}):{cfg['gnmi_port']}")
print()

with gNMIclient(
    target=target,
    username=cfg["username"],
    password=cfg["password"],
    insecure=True,
) as client:

    # 1. gNMI Capabilities
    print("[1] gNMI Capabilities Discovery")
    print("-" * 40)
    caps = client.capabilities()
    print(f"gNMI version: {caps.get('gnmi_version', 'unknown')}")
    print(f"Supported encodings: {caps.get('supported_encodings', [])}")
    models = caps.get("supported_models", [])
    print(f"Supported YANG models: {len(models)}")
    for m in models[:5]:
        print(f"  - {m['name']} v{m['version']}")
    print(f"  ... and {len(models) - 5} more")
    print()

    # 2. Get interfaces data
    print("[2] gNMI Get: interfaces")
    print("-" * 40)
    data = client.get(path=["interfaces"])
    notif = data["notification"][0]
    timestamp = notif["timestamp"]
    updates = notif["update"]

    print(f"Timestamp: {timestamp}")
    print(f"Update count: {len(updates)}")

    # The first update contains the interfaces container
    if updates:
        interfaces_val = updates[0]["val"]
        intf_list = interfaces_val.get("interface", [])
        print(f"Interfaces: {len(intf_list)}")

        for intf in intf_list:
            name = intf.get("name", "?")
            state = intf.get("state", {})
            oper_status = state.get("oper-status", "?")
            admin_status = state.get("admin-status", "?")
            mtu = state.get("mtu", "?")
            desc = state.get("description", "")
            print(f"  {name}")
            print(f"    Admin: {admin_status}, Oper: {oper_status}, MTU: {mtu}")
            if desc:
                print(f"    Description: {desc}")

            # Interface counters
            counters = state.get("counters", {})
            in_pkts = counters.get("in-pkts", "N/A")
            out_pkts = counters.get("out-pkts", "N/A")
            if in_pkts != "N/A":
                print(f"    In pkts: {in_pkts}, Out pkts: {out_pkts}")

            # IP addresses
            subs = intf.get("subinterfaces", {}).get("subinterface", [])
            for sub in subs:
                ipv4 = sub.get("openconfig-if-ip:ipv4", {})
                addrs = ipv4.get("addresses", {}).get("address", [])
                for addr in addrs:
                    print(f"    IP: {addr['ip']}/{addr['state']['prefix-length']}")

    # 3. Get system data
    print(f"\n[3] gNMI Get: system")
    print("-" * 40)
    data = client.get(path=["system"])
    notif = data["notification"][0]
    sys_updates = notif["update"]
    if sys_updates:
        sys_val = sys_updates[0]["val"]
        print(f"System data keys: {list(sys_val.keys())[:5]}")

    # 4. Get routing policy
    print(f"\n[4] gNMI Get: routing-policy")
    print("-" * 40)
    data = client.get(path=["routing-policy"])
    print(f"Response: {len(str(data))} chars")
    print("(Route policies define path selection rules for BGP/OSPF/ISIS)")

    # 5. Get LLDP neighbors
    print(f"\n[5] gNMI Get: lldp (neighbor discovery)")
    print("-" * 40)
    data = client.get(path=["lldp"])
    notif = data["notification"][0]
    lldp_updates = notif["update"]
    if lldp_updates:
        print(f"LLDP data: {len(str(data))} chars")

    print("\nKey takeaways:")
    print("  - gNMI uses gRPC (HTTP/2 + protobuf) instead of SSH+XML (NETCONF)")
    print("  - pygnmi automatically converts protobuf to Python dicts")
    print("  - gNMI paths use OpenConfig model structure (e.g., 'interfaces')")
    print("  - Each response has timestamp, prefix, and update list")
    print("  - gNMI is faster for streaming telemetry; NETCONF is better for config")
