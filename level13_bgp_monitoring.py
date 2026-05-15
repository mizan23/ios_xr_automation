#!/usr/bin/env python3
"""
LEVEL 13: BGP Monitoring & Analysis via NETCONF + gNMI
=========================================================
Topics covered:
  - BGP operational state via gNMI OpenConfig
  - BGP configuration via NETCONF
  - Neighbor state analysis (Established, Idle, Active)
  - BGP table inspection (prefixes, paths)
  - Route policy analysis
  - BGP session troubleshooting automation
"""
import socket
import json
from lxml import etree
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])
target = (ip, str(cfg["gnmi_port"]))

print("=" * 60)
print("LEVEL 13: BGP Monitoring & Analysis")
print("=" * 60)


def analyze_bgp_operational(client):
    """Analyze BGP operational state via gNMI."""
    print("\n[1] BGP Operational State (gNMI)")
    print("-" * 40)

    data = client.get(path=["network-instances"])
    notif = data["notification"][0]

    for update in notif["update"]:
        instances = update["val"].get("network-instance", [])
        for inst in instances:
            protocols = inst.get("protocols", {}).get("protocol", [])
            for proto in protocols:
                if proto.get("identifier") == "openconfig-policy-types:BGP":
                    bgp = proto.get("bgp", {})
                    global_data = bgp.get("global", {})
                    gstate = global_data.get("state", {})

                    print(f"\nBGP Instance: {inst['name']}")
                    if gstate:
                        print(f"  ASN: {gstate.get('as', 'N/A')}")
                        print(f"  Router-ID: {gstate.get('router-id', 'N/A')}")
                        print(f"  Total paths: {gstate.get('total-paths', 0)}")
                        print(f"  Total prefixes: {gstate.get('total-prefixes', 0)}")

                    neighbors = bgp.get("neighbors", {}).get("neighbor", [])
                    print(f"\n  BGP Neighbors ({len(neighbors)}):")
                    print(f"  {'Neighbor':<20} {'State':<12} {'AS':<8} "
                          f"{'Up/Down':<15} {'Sent':<8} {'Recv':<8}")
                    print(f"  {'-'*70}")

                    for n in neighbors:
                        nstate = n.get("state", {})
                        addr = nstate.get("neighbor-address", "?")
                        session_st = nstate.get("session-state", "?").upper()
                        peer_as = nstate.get("peer-as", "?")
                        last_est = nstate.get("last-established", "0")
                        msgs = nstate.get("messages", {})
                        sent = msgs.get("sent", {}).get("UPDATE", "0")
                        recv = msgs.get("received", {}).get("UPDATE", "0")

                        # Session state color coding via symbols
                        indicator = {
                            "ESTABLISHED": "[UP]",
                            "IDLE": "[!!]",
                            "ACTIVE": "[..]",
                            "CONNECT": "[..]",
                        }.get(session_st, "[?]")

                        print(f"  {indicator} {addr:<17} {session_st:<12} "
                              f"{peer_as:<8} {last_est[:10]:<15} "
                              f"{sent:<8} {recv:<8}")

                        # Detailed AFI-SAFI info
                        afi_safis = n.get("afi-safis", {}).get("afi-safi", [])
                        for afi in afi_safis:
                            as_name = afi.get("afi-safi-name", "")
                            as_state = afi.get("state", {})
                            if as_state.get("active"):
                                pref = as_state.get("prefixes", {})
                                print(f"    AFI: {as_name} "
                                      f"(received: {pref.get('received', 0)}, "
                                      f"installed: {pref.get('installed', 0)})")


def analyze_bgp_config(session):
    """Analyze BGP configuration via NETCONF."""
    print("\n[2] BGP Configuration (NETCONF)")
    print("-" * 40)

    # Try Cisco native BGP config
    bgp_filter = """
    <filter>
      <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"/>
    </filter>
    """
    try:
        resp = session.get_config(source="running", filter=bgp_filter)
        xml = etree.fromstring(str(resp))
        bgp_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"
        bgp_elem = xml.find(f".//{{{bgp_ns}}}bgp")

        if bgp_elem is not None:
            print("BGP configuration found (Cisco native model)")
            instance = bgp_elem.find(f"{{{bgp_ns}}}instance")
            if instance is not None:
                as_elem = instance.find(f"{{{bgp_ns}}}instance-as")
                if as_elem is not None:
                    for child in as_elem:
                        if child.tag.endswith("}as"):
                            print(f"  BGP AS Number (list): {child[0].text if len(child) else 'N/A'}")
        else:
            print("No Cisco-native BGP config found (expected - using unified model)")
    except Exception as e:
        print(f"BGP config query: {e}")

    # Unified model BGP
    print("\nSearching unified model BGP...")
    um_filter = """
    <filter>
      <router-bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-um-router-bgp-cfg"/>
    </filter>
    """
    try:
        resp = session.get_config(source="running", filter=um_filter)
        print(f"Unified BGP config: {len(str(resp))} chars")
    except Exception as e:
        print(f"Unified model: {e}")


def bgp_health_summary(client):
    """Generate BGP health summary."""
    print("\n[3] BGP Health Summary")
    print("-" * 40)
    data = client.get(path=["network-instances"])
    notif = data["notification"][0]

    established = 0
    non_established = 0
    total_prefixes = 0

    for update in notif["update"]:
        instances = update["val"].get("network-instance", [])
        for inst in instances:
            protocols = inst.get("protocols", {}).get("protocol", [])
            for proto in protocols:
                if proto.get("identifier") == "openconfig-policy-types:BGP":
                    bgp = proto.get("bgp", {})
                    total_prefixes += bgp.get("global", {}).get(
                        "state", {}).get("total-prefixes", 0)
                    neighbors = bgp.get("neighbors", {}).get("neighbor", [])
                    for n in neighbors:
                        state = n.get("state", {}).get("session-state", "")
                        if state == "ESTABLISHED":
                            established += 1
                        else:
                            non_established += 1

    print(f"  Established sessions: {established}")
    print(f"  Non-established: {non_established}")
    print(f"  Total BGP prefixes: {total_prefixes}")
    health = "HEALTHY" if non_established == 0 and established > 0 else "DEGRADED"
    print(f"  Overall: {health}")


# --- Execute ---
with gNMIclient(
    target=target, username=cfg["username"], password=cfg["password"],
    insecure=True,
) as gc:
    analyze_bgp_operational(gc)
    bgp_health_summary(gc)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as nc:
    analyze_bgp_config(nc)

print("\nKey takeaways:")
print("  - gNMI/OpenConfig gives vendor-neutral BGP state (portable across platforms)")
print("  - NETCONF gives device-specific BGP configuration")
print("  - Track session-state transitions for BGP troubleshooting")
print("  - AFI-SAFI prefix counts reveal routing table health")
print("  - This pattern works for OSPF, ISIS, MPLS-TE, and other protocols")
