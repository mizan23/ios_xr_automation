#!/usr/bin/env python3
"""
LEVEL 12: Multi-Device & Bulk Operations
===========================================
Topics covered:
  - Device inventory management
  - Parallel operations via threading
  - Bulk configuration deployment
  - Device-specific configuration templating
  - Aggregated reporting across devices
"""
import socket
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ncclient import manager
from config import load_xr_config

print("=" * 60)
print("LEVEL 12: Multi-Device & Bulk Operations")
print("=" * 60)

# --- Device Inventory (in production, this comes from NetBox/CMDB) ---
# We'll simulate multiple devices using the same sandbox
inventory = [
    {
        "name": "sandbox-iosxr-1",
        "hostname": "sandbox-iosxr-1.cisco.com",
        "netconf_port": 830,
        "gnmi_port": 57777,
        "role": "PE",
        "vendor": "cisco-xr",
    },
    {
        "name": "sandbox-iosxr-1-alt",
        "hostname": "sandbox-iosxr-1.cisco.com",
        "netconf_port": 830,
        "gnmi_port": 57777,
        "role": "P",
        "vendor": "cisco-xr",
    },
]

cfg = load_xr_config()


def check_device(device_info, creds):
    """Check connectivity and collect basic info from one device."""
    try:
        ip = socket.gethostbyname(device_info["hostname"])
        with manager.connect(
            host=ip, port=device_info["netconf_port"],
            username=creds["username"], password=creds["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=10,
        ) as session:
            caps = len(session.server_capabilities)
            return {
                "device": device_info["name"],
                "status": "reachable",
                "ip": ip,
                "capabilities": caps,
                "session_id": session.session_id,
            }
    except Exception as e:
        return {
            "device": device_info["name"],
            "status": "failed",
            "error": str(e)[:80],
        }


def get_device_interfaces(device_info, creds):
    """Get interfaces from one device."""
    try:
        ip = socket.gethostbyname(device_info["hostname"])
        with manager.connect(
            host=ip, port=device_info["netconf_port"],
            username=creds["username"], password=creds["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=10,
        ) as session:
            from lxml import etree
            filter_xml = """
            <filter>
              <interface-configurations
                xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/>
            </filter>
            """
            resp = session.get_config(source="running", filter=filter_xml)
            xml = etree.fromstring(str(resp))
            ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
            interfaces = []
            for intf in xml.findall(f".//{{{ns}}}interface-configuration"):
                active = intf.find(f"{{{ns}}}active")
                if active is not None:
                    interfaces.append(active.text)
            return {"device": device_info["name"], "interfaces": interfaces}
    except Exception as e:
        return {"device": device_info["name"], "error": str(e)[:80]}


# --- Parallel operations demonstration ---
print("\n[1] Sequential vs Parallel Device Checks")
print("-" * 40)

# Sequential
start = time.time()
seq_results = [check_device(d, cfg) for d in inventory]
seq_time = time.time() - start
print(f"Sequential: {seq_time:.2f}s")

# Parallel
start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(check_device, d, cfg): d for d in inventory}
    par_results = []
    for future in as_completed(futures):
        par_results.append(future.result())
par_time = time.time() - start
print(f"Parallel: {par_time:.2f}s")
print(f"Speedup: {seq_time / par_time:.1f}x")

# --- Results display ---
print(f"\n[2] Device Health Report")
print("-" * 40)
print(f"{'Device':<25} {'Status':<12} {'IP':<18} {'Caps':<8}")
print("-" * 65)
for r in par_results:
    if r["status"] == "reachable":
        print(f"{r['device']:<25} {r['status']:<12} {r['ip']:<18} {r['capabilities']:<8}")
    else:
        print(f"{r['device']:<25} {r['status']:<12} {'-':<18} {'-':<8}")
        print(f"  Error: {r.get('error', '')}")

# --- Bulk interface collection ---
print(f"\n[3] Bulk Interface Collection")
print("-" * 40)
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(get_device_interfaces, d, cfg) for d in inventory]
    for future in as_completed(futures):
        result = future.result()
        if "interfaces" in result:
            print(f"\n{result['device']}: {len(result['interfaces'])} interfaces")
            for intf in result["interfaces"][:5]:
                print(f"  - {intf}")
        else:
            print(f"\n{result['device']}: Error - {result.get('error')}")

# --- Configuration template engine demo ---
print(f"\n[4] Configuration Template Engine (Conceptual)")
print("-" * 40)
interface_template = """
<interface-configurations xmlns="{ns}">
  <interface-configuration>
    <active>{if_name}</active>
    <description>{description}</description>
    <interface-virtual/>
  </interface-configuration>
</interface-configurations>
"""

# Render templates for each device
for device in inventory:
    rendered = interface_template.format(
        ns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg",
        if_name=f"Loopback{hash(device['name']) % 1000}",
        description=f"Auto-configured for {device['name']} ({device['role']})",
    )
    print(f"\nTemplate for {device['name']} ({device['role']}):")
    print(f"  {rendered[:120]}...")

print("\nKey takeaways:")
print("  - ThreadPoolExecutor for parallel device operations")
print("  - Device inventory defines what to manage (single source of truth)")
print("  - Templates render device-specific configuration")
print("  - Bulk operations require proper error isolation (one failure != all)")
print("  - In production, use async/await (asyncio) for better scalability")
