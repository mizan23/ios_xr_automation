#!/usr/bin/env python3
"""
LEVEL 4: NETCONF XPath Filters
================================
Topics covered:
  - XPath filter syntax vs subtree filters
  - Selecting nodes by path
  - XPath predicates (conditions)
  - Position-based selection
  - When to use XPath vs subtree filters
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 4: NETCONF XPath Filters")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # XPath 1: Get specific interface by name
    print("\n[1] XPath: Get Loopback0 interface config")
    print("-" * 40)
    xpath1 = "/ifmgr-cfg:interface-configurations/ifmgr-cfg:interface-configuration[ifmgr-cfg:active='Loopback0']"
    ns_map1 = {"ifmgr-cfg": "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"}
    try:
        resp1 = session.get_config(source="running", filter=("xpath", xpath1))
        xml1 = etree.fromstring(str(resp1))
        print(f"Response: {len(str(resp1))} chars")
        print(etree.tostring(xml1, pretty_print=True).decode()[:800])
    except Exception as e:
        print(f"XPath error: {e}")

    # XPath 2: Get GigabitEthernet0/0/0/0
    print("\n[2] XPath: Get GigabitEthernet0/0/0/0")
    print("-" * 40)
    xpath2 = "/ifmgr-cfg:interface-configurations/ifmgr-cfg:interface-configuration[ifmgr-cfg:active='GigabitEthernet0/0/0/0']"
    try:
        resp2 = session.get_config(source="running", filter=("xpath", xpath2))
        print(f"Response: {len(str(resp2))} chars")
    except Exception as e:
        print(f"XPath error: {e}")

    # XPath 3: Get all Loopback interfaces (name contains 'Loopback')
    print("\n[3] XPath: All Loopback interfaces (starts-with)")
    print("-" * 40)
    xpath3 = "/ifmgr-cfg:interface-configurations/ifmgr-cfg:interface-configuration[starts-with(ifmgr-cfg:active,'Loopback')]"
    try:
        resp3 = session.get_config(source="running", filter=("xpath", xpath3))
        xml3 = etree.fromstring(str(resp3))
        loopbacks = xml3.findall(f".//{{{ns_map1['ifmgr-cfg']}}}interface-configuration")
        print(f"Loopback interfaces found: {len(loopbacks)}")
        for lb in loopbacks:
            active = lb.find(f"{{{ns_map1['ifmgr-cfg']}}}active")
            if active is not None:
                print(f"  - {active.text}")
    except Exception as e:
        print(f"XPath error: {e}")

    # XPath 4: Position-based - first interface
    print("\n[4] XPath: First interface by position")
    print("-" * 40)
    xpath4 = "/ifmgr-cfg:interface-configurations/ifmgr-cfg:interface-configuration[1]"
    try:
        resp4 = session.get_config(source="running", filter=("xpath", xpath4))
        print(f"Response: {len(str(resp4))} chars")
    except Exception as e:
        print(f"XPath error: {e}")

    # XPath 5: Get BGP neighbor config via Cisco model
    print("\n[5] XPath: BGP configuration")
    print("-" * 40)
    xpath5 = "/ipv4-bgp-cfg:bgp/ipv4-bgp-cfg:instance"
    ns_map5 = {"ipv4-bgp-cfg": "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"}
    try:
        resp5 = session.get_config(source="running", filter=("xpath", xpath5))
        print(f"BGP config: {len(str(resp5))} chars")
    except Exception as e:
        print(f"XPath error: {e}")

    # XPath 6: Operational data with XPath
    print("\n[6] XPath on operational data: interface/state/type")
    print("-" * 40)
    xpath6 = "/oc-if:interfaces/oc-if:interface/oc-if:state/oc-if:type"
    ns_map6 = {"oc-if": "http://openconfig.net/yang/interfaces"}
    try:
        resp6 = session.get(filter=("xpath", xpath6))
        xml6 = etree.fromstring(str(resp6))
        types = xml6.findall(f".//{{{ns_map6['oc-if']}}}type")
        for t in types[:5]:
            if t.text:
                print(f"  {t.text}")
    except Exception as e:
        print(f"XPath error: {e}")

    print("\nKey takeaways:")
    print("  - XPath filter: filter=('xpath', '<expression>')")
    print("  - Subtree filter: filter='<xml>...</xml>'")
    print("  - XPath is better for conditional selection and complex queries")
    print("  - Subtree is simpler for basic containment filtering")
    print("  - Namespace prefixes in XPath must match the namespace map")
    print("  - Not all devices support all XPath functions (e.g., contains())")
