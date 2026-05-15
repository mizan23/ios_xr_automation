#!/usr/bin/env python3
"""
LEVEL 1: NETCONF Basics - Connect, Capabilities, and Session Management
=======================================================================
Topics covered:
  - DNS resolution for network devices
  - NETCONF session establishment via ncclient
  - Server capabilities exploration (YANG model discovery)
  - IETF standard capabilities vs vendor extensions
  - Proper session cleanup with context managers
"""
import socket
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 1: NETCONF Connection & Capabilities")
print("=" * 60)
print(f"Device: {cfg['hostname']}")
print(f"Resolved IP: {ip}")
print(f"NETCONF Port: {cfg['netconf_port']}")
print(f"Username: {cfg['username']}")
print()

with manager.connect(
    host=ip,
    port=cfg["netconf_port"],
    username=cfg["username"],
    password=cfg["password"],
    hostkey_verify=False,
    device_params={"name": "iosxr"},
) as session:
    print(f"Session ID: {session.session_id}")
    print(f"Connected: {session.connected}")
    print()

    caps = session.server_capabilities
    print(f"Total capabilities advertised: {len(caps)}")
    print()

    # Categorize capabilities
    categories = {
        "IETF Standard": [],
        "OpenConfig": [],
        "Cisco Native": [],
        "Other": [],
    }
    for cap in caps:
        if cap.startswith("urn:ietf"):
            categories["IETF Standard"].append(cap)
        elif "openconfig" in cap.lower():
            categories["OpenConfig"].append(cap)
        elif "cisco" in cap.lower():
            categories["Cisco Native"].append(cap)
        else:
            categories["Other"].append(cap)

    for cat, items in categories.items():
        if items:
            print(f"--- {cat} ({len(items)}) ---")
            for item in items[:3]:
                print(f"  {item}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more")
            print()

    # IETF standard capabilities (these tell us what operations are supported)
    print("--- IETF Standard Capabilities ---")
    ietf_ops = {
        "urn:ietf:params:netconf:base:1.1": "NETCONF 1.1 (base protocol)",
        "urn:ietf:params:netconf:capability:candidate:1.0": "Candidate configuration datastore",
        "urn:ietf:params:netconf:capability:rollback-on-error:1.0": "Rollback on error",
        "urn:ietf:params:netconf:capability:validate:1.1": "Configuration validation",
        "urn:ietf:params:netconf:capability:confirmed-commit:1.1": "Confirmed commit (auto-rollback)",
        "urn:ietf:params:netconf:capability:notification:1.0": "NETCONF notifications",
        "urn:ietf:params:netconf:capability:interleave:1.0": "Interleaved operations",
    }
    for uri, desc in ietf_ops.items():
        if uri in caps:
            print(f"  {desc}")
    print()

    print("Key takeaways:")
    print("  - ncclient handles SSH transport, XML encoding, and NETCONF framing")
    print("  - device_params={'name':'iosxr'} tells ncclient this is IOS XR")
    print("  - hostkey_verify=False is for lab/sandbox only")
    print("  - Capabilities show which YANG models and NETCONF features are available")
