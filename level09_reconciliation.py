#!/usr/bin/env python3
"""
LEVEL 9: Network State Reconciliation - NETCONF + gNMI
========================================================
Topics covered:
  - Comparing NETCONF (intended config) vs gNMI (actual state)
  - Detecting configuration drift
  - Interface state validation across protocols
  - Unified data model across NETCONF and gNMI
  - Building a reconciliation report
"""
import socket
import json
from lxml import etree
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 9: State Reconciliation (NETCONF + gNMI)")
print("=" * 60)

# --- Phase 1: Get intended config via NETCONF ---
print("\n--- Phase 1: NETCONF - Intended Interface Config ---")
netconf_interfaces = {}
with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as nc:
    nc_filter = """
    <filter>
      <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/>
    </filter>
    """
    resp = nc.get_config(source="running", filter=nc_filter)
    xml = etree.fromstring(str(resp))
    ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    for intf in xml.findall(f".//{{{ns}}}interface-configuration"):
        active = intf.find(f"{{{ns}}}active")
        desc = intf.find(f"{{{ns}}}description")
        name = active.text if active is not None else "?"
        netconf_interfaces[name] = {
            "description": desc.text if desc is not None else "",
        }
    print(f"NETCONF interfaces: {len(netconf_interfaces)}")

# --- Phase 2: Get operational state via gNMI ---
print("\n--- Phase 2: gNMI - Operational Interface State ---")
gnmi_state = {}
with gNMIclient(
    target=(ip, str(cfg["gnmi_port"])),
    username=cfg["username"], password=cfg["password"],
    insecure=True,
) as gc:
    data = gc.get(path=["interfaces"])
    notif = data["notification"][0]
    for update in notif["update"]:
        intf_list = update["val"].get("interface", [])
        for intf in intf_list:
            name = intf["name"]
            state = intf.get("state", {})
            gnmi_state[name] = {
                "oper_status": state.get("oper-status", "?"),
                "admin_status": state.get("admin-status", "?"),
                "description": state.get("description", ""),
                "mtu": state.get("mtu", 0),
            }
    print(f"gNMI interfaces: {len(gnmi_state)}")

# --- Phase 3: Reconcile ---
print("\n--- Phase 3: Reconciliation Report ---")
print(f"{'Interface':<30} {'Config':<8} {'Oper':<8} {'Drift':<10}")
print("-" * 65)

issues = []

for name in sorted(set(list(netconf_interfaces.keys()) + list(gnmi_state.keys()))):
    nc_data = netconf_interfaces.get(name, {})
    gn_data = gnmi_state.get(name, {})

    nc_status = "Config" if name in netconf_interfaces else "None"
    op_status = gn_data.get("oper_status", "N/A")

    # Check for issues
    drift_flags = []
    if name in netconf_interfaces and name in gnmi_state:
        if gn_data.get("admin_status") == "UP" and op_status != "UP":
            drift_flags.append("DOWN!")
        nc_desc = nc_data.get("description", "")
        gn_desc = gn_data.get("description", "")
        if nc_desc != gn_desc and nc_desc:
            drift_flags.append("DESC")
    elif name in netconf_interfaces and name not in gnmi_state:
        drift_flags.append("NO_STATE")
    elif name not in netconf_interfaces and name in gnmi_state:
        drift_flags.append("NO_CONFIG")

    drift = ", ".join(drift_flags) if drift_flags else "OK"
    if drift_flags:
        issues.append((name, drift))

    print(f"{name:<30} {nc_status:<8} {op_status:<8} {drift:<10}")

print(f"\nIssues found: {len(issues)}")
for name, drift in issues:
    print(f"  {name}: {drift}")

print("\nKey takeaways:")
print("  - NETCONF gives intended config; gNMI gives operational truth")
print("  - Reconciliation detects config drift and operational failures")
print("  - Combined approach enables closed-loop automation")
print("  - This pattern scales to multi-vendor and multi-device")
