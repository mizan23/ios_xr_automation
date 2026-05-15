#!/usr/bin/env python3
"""
LEVEL 2: NETCONF Get-Config - Retrieving Configuration Datastores
==================================================================
Topics covered:
  - get_config() with different datastores (running, candidate, startup)
  - Understanding XML configuration structure
  - Configuration size analysis
  - Parsing XML responses with lxml
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 2: NETCONF Get-Config Operations")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # 1. Get running configuration
    print("\n[1] get_config(source='running')")
    print("-" * 40)
    running = session.get_config(source="running")
    running_xml = etree.fromstring(str(running))
    print(f"Raw XML size: {len(str(running))} chars")

    # Count top-level elements
    ns = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}
    data = running_xml.find(".//nc:data", ns)
    if data is not None:
        children = list(data)
        print(f"Top-level config sections: {len(children)}")
        for child in children[:8]:
            tag = etree.QName(child).localname
            print(f"  - {tag}")

    # 2. Parse specific config sections
    print("\n[2] Extracting hostname from config")
    print("-" * 40)
    hostname_elem = running_xml.find(".//{http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-cfg}hostname")
    if hostname_elem is not None:
        print(f"Device hostname: {hostname_elem.text}")

    # 3. Parse interface configuration
    print("\n[3] Interface configuration summary")
    print("-" * 40)
    # Cisco native interface model
    if_cfg_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    interfaces = running_xml.findall(f".//{{{if_cfg_ns}}}interface-configuration")
    print(f"Interfaces configured (Cisco native): {len(interfaces)}")

    for intf in interfaces[:5]:
        name_elem = intf.find(f"{{{if_cfg_ns}}}interface-name")
        name = name_elem.text if name_elem is not None else "unknown"
        print(f"  - {name}")

    # 4. Using get() for operational data
    print("\n[4] get() - operational data (interface-state)")
    print("-" * 40)
    op_filter = """
    <filter>
      <interfaces xmlns="http://openconfig.net/yang/interfaces"/>
    </filter>
    """
    op_data = session.get(filter=op_filter)
    print(f"Operational data size: {len(str(op_data))} chars")

    op_xml = etree.fromstring(str(op_data))
    oc_ns = "http://openconfig.net/yang/interfaces"
    intf_names = op_xml.findall(f".//{{{oc_ns}}}interface/{{{oc_ns}}}name")
    print(f"Interfaces discovered: {len(intf_names)}")
    for name in intf_names[:6]:
        print(f"  - {name.text}")

    print("\nKey takeaways:")
    print("  - get_config() pulls configuration; get() pulls state+config")
    print("  - source='running' gives current active config")
    print("  - lxml.etree parses NETCONF XML responses for programmatic access")
    print("  - XML namespaces are critical for correct element selection")
