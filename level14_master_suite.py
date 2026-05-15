#!/usr/bin/env python3
"""
LEVEL 14: Master Automation Suite - Full CLI Tool
=====================================================
Topics covered:
  - CLI-driven automation framework
  - Modular architecture (config, collectors, analyzers, reporters)
  - Comprehensive reporting (text + JSON + CSV)
  - Scheduled operations
  - Plugin architecture for extensibility
  - Integration patterns for CI/CD pipelines

This is the capstone - a production-style automation suite combining
everything from levels 1-13 into a single operational tool.
"""
import socket
import json
import time
import sys
import csv
from datetime import datetime
from lxml import etree
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
cfg = load_xr_config()
IP = socket.gethostbyname(cfg["hostname"])

# ---------------------------------------------------------------------------
# Connection Helpers
# ---------------------------------------------------------------------------
def netconf_connect():
    return manager.connect(
        host=IP, port=cfg["netconf_port"],
        username=cfg["username"], password=cfg["password"],
        hostkey_verify=False, device_params={"name": "iosxr"},
        timeout=15,
    )

def gnmi_connect():
    client = gNMIclient(
        target=(IP, str(cfg["gnmi_port"])),
        username=cfg["username"], password=cfg["password"],
        insecure=True,
    )
    client.connect()
    return client

# ---------------------------------------------------------------------------
# Collectors (gather data)
# ---------------------------------------------------------------------------
def collect_interfaces_nc(session):
    """Collect interface configuration via NETCONF."""
    fltr = '<filter><interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/></filter>'
    resp = session.get_config(source="running", filter=fltr)
    xml = etree.fromstring(str(resp))
    ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    result = []
    for intf in xml.findall(f".//{{{ns}}}interface-configuration"):
        active = intf.find(f"{{{ns}}}active")
        desc = intf.find(f"{{{ns}}}description")
        result.append({
            "name": active.text if active is not None else "?",
            "description": desc.text if desc is not None else "",
        })
    return result

def collect_interfaces_gn(client):
    """Collect interface operational state via gNMI."""
    data = client.get(path=["interfaces"])
    notif = data["notification"][0]
    result = []
    for update in notif["update"]:
        for intf in update["val"].get("interface", []):
            state = intf.get("state", {})
            counters = state.get("counters", {})
            subs = intf.get("subinterfaces", {}).get("subinterface", [])
            ips = []
            for sub in subs:
                for addr in sub.get("openconfig-if-ip:ipv4", {}).get(
                    "addresses", {}).get("address", []):
                    ips.append(f"{addr['ip']}/{addr['state']['prefix-length']}")
            result.append({
                "name": intf["name"],
                "admin_status": state.get("admin-status", ""),
                "oper_status": state.get("oper-status", ""),
                "mtu": state.get("mtu", 0),
                "description": state.get("description", ""),
                "in_pkts": int(counters.get("in-pkts", 0)),
                "out_pkts": int(counters.get("out-pkts", 0)),
                "ip_addresses": ips,
            })
    return result

def collect_bgp_gn(client):
    """Collect BGP state via gNMI."""
    data = client.get(path=["network-instances"])
    notif = data["notification"][0]
    result = {"instances": [], "neighbors": []}
    for update in notif["update"]:
        for inst in update["val"].get("network-instance", []):
            for proto in inst.get("protocols", {}).get("protocol", []):
                if proto.get("identifier") == "openconfig-policy-types:BGP":
                    bgp = proto.get("bgp", {})
                    result["instances"].append({
                        "name": inst["name"],
                        "asn": bgp.get("global", {}).get("state", {}).get("as", 0),
                        "router_id": bgp.get("global", {}).get("state", {}).get("router-id", ""),
                    })
                    for n in bgp.get("neighbors", {}).get("neighbor", []):
                        nstate = n.get("state", {})
                        result["neighbors"].append({
                            "address": nstate.get("neighbor-address", ""),
                            "state": nstate.get("session-state", ""),
                            "peer_as": nstate.get("peer-as", 0),
                        })
    return result

def collect_system_gn(client):
    """Collect system state via gNMI."""
    data = client.get(path=["system"])
    return len(str(data))

# ---------------------------------------------------------------------------
# Analyzers
# ---------------------------------------------------------------------------
def analyze_interfaces(nc_ifaces, gn_ifaces):
    """Cross-reference config vs operational state."""
    gn_map = {i["name"]: i for i in gn_ifaces}
    report = []
    for nc in nc_ifaces:
        gn = gn_map.get(nc["name"])
        issues = []
        if gn:
            if gn["admin_status"] == "UP" and gn["oper_status"] != "UP":
                issues.append("DOWN")
            if nc["description"] != gn["description"] and nc["description"]:
                issues.append("DESC_MISMATCH")
        else:
            issues.append("NO_OPER_STATE")
        report.append({
            "name": nc["name"],
            "oper_status": gn["oper_status"] if gn else "N/A",
            "issues": issues if issues else ["OK"],
        })
    return report

# ---------------------------------------------------------------------------
# Reporters (output formats)
# ---------------------------------------------------------------------------
def report_text(title, data, columns):
    """Text table report."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    header = "  ".join(f"{c:<20}" for c in columns)
    print(f"  {header}")
    print(f"  {'-'*65}")
    for row in data[:20]:
        vals = [str(row.get(c, ""))[:18] for c in columns]
        print(f"  " + "  ".join(f"{v:<20}" for v in vals))
    print(f"  Total: {len(data)} items")

def report_json(filename, data):
    """Export to JSON file."""
    path = f"report_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  JSON exported: {path}")

def report_csv(filename, data):
    """Export to CSV file."""
    if not data:
        return
    path = f"report_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  CSV exported: {path}")

# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------
def cmd_interfaces():
    """Full interface report: NETCONF config + gNMI state."""
    print("\n>>> Collecting interface data...")
    with netconf_connect() as nc:
        nc_data = collect_interfaces_nc(nc)
    with gnmi_connect() as gc:
        gn_data = collect_interfaces_gn(gc)
        gc.close()

    analysis = analyze_interfaces(nc_data, gn_data)
    report_text("Interface Health Report", analysis,
                 ["name", "oper_status", "issues"])
    report_json("interfaces", gn_data)
    
    issues = [a for a in analysis if a["issues"] != ["OK"]]
    if issues:
        print(f"\n  FLAGGED: {len(issues)} interfaces with issues")

def cmd_bgp():
    """BGP state and neighbor report."""
    print("\n>>> Collecting BGP data...")
    with gnmi_connect() as gc:
        bgp_data = collect_bgp_gn(gc)
        gc.close()

    for inst in bgp_data["instances"]:
        print(f"\n  BGP Instance: ASN {inst['asn']}, Router-ID {inst['router_id']}")
    
    report_text("BGP Neighbors", bgp_data["neighbors"],
                 ["address", "state", "peer_as"])
    report_json("bgp", bgp_data)

def cmd_full_report():
    """Generate comprehensive device report."""
    print("\n>>> Generating full device report...")
    start = time.time()

    with netconf_connect() as nc:
        nc_ifaces = collect_interfaces_nc(nc)
    with gnmi_connect() as gc:
        gn_ifaces = collect_interfaces_gn(gc)
        bgp = collect_bgp_gn(gc)
        sys_size = collect_system_gn(gc)
        gc.close()

    full_report = {
        "device": cfg["hostname"],
        "generated_at": datetime.now().isoformat(),
        "collection_duration_s": round(time.time() - start, 2),
        "netconf_interfaces": len(nc_ifaces),
        "gnmi_interfaces": len(gn_ifaces),
        "bgp_neighbors": len(bgp["neighbors"]),
        "bgp_neighbors_established": sum(
            1 for n in bgp["neighbors"] if n["state"] == "ESTABLISHED"),
        "interfaces": gn_ifaces,
        "bgp": bgp,
        "interface_analysis": analyze_interfaces(nc_ifaces, gn_ifaces),
    }

    print(f"\n  Device: {cfg['hostname']}")
    print(f"  NETCONF interfaces: {full_report['netconf_interfaces']}")
    print(f"  gNMI interfaces: {full_report['gnmi_interfaces']}")
    print(f"  BGP neighbors: {full_report['bgp_neighbors']} "
          f"({full_report['bgp_neighbors_established']} established)")
    print(f"  Collection time: {full_report['collection_duration_s']}s")

    report_json("full", full_report)
    return full_report

def cmd_menu():
    """Display interactive menu."""
    print("=" * 60)
    print("  IOS XR Master Automation Suite")
    print("=" * 60)
    print(f"  Device: {cfg['hostname']} ({IP})")
    print()
    print("  Commands:")
    print("    python level14_master_suite.py interfaces   - Interface report")
    print("    python level14_master_suite.py bgp          - BGP report")
    print("    python level14_master_suite.py full         - Full device report")
    print("    python level14_master_suite.py health       - Quick health check")
    print("    python level14_master_suite.py menu         - This menu")
    print()

def cmd_health():
    """Quick health check."""
    print("\n>>> Health Check...")
    try:
        with netconf_connect() as nc:
            print(f"  NETCONF: OK (session {nc.session_id})")
    except Exception as e:
        print(f"  NETCONF: FAIL - {e}")

    try:
        with gnmi_connect() as gc:
            caps = gc.capabilities()
            print(f"  gNMI: OK ({len(caps.get('supported_models', []))} models)")
            gc.close()
    except Exception as e:
        print(f"  gNMI: FAIL - {e}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
COMMANDS = {
    "interfaces": cmd_interfaces,
    "bgp": cmd_bgp,
    "full": cmd_full_report,
    "health": cmd_health,
    "menu": cmd_menu,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "menu"
    handler = COMMANDS.get(cmd, cmd_menu)
    try:
        handler()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        sys.exit(1)
