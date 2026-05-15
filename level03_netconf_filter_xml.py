#!/usr/bin/env python3
"""
LEVEL 3: NETCONF XML Subtree Filters
=====================================
Topics covered:
  - Subtree filter syntax (empty tags = select-all, content = match)
  - Filtering by containment hierarchy
  - Attribute match filters
  - Selecting specific leaf nodes
  - Combining filters across namespaces
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 3: NETCONF Subtree Filters (XML)")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # FILTER 1: Simple containment filter - all interfaces
    print("\n[1] Simple containment: all interfaces (Cisco native)")
    print("-" * 40)
    filter1 = """
    <filter>
      <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/>
    </filter>
    """
    resp1 = session.get_config(source="running", filter=filter1)
    xml1 = etree.fromstring(str(resp1))
    if_cfg_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    intfs = xml1.findall(f".//{{{if_cfg_ns}}}interface-configuration")
    print(f"Interfaces found: {len(intfs)}")
    for intf in intfs:
        active = intf.find(f"{{{if_cfg_ns}}}active")
        name = active.text if active is not None else "?"
        print(f"  {name}")

    # FILTER 2: Specific leaf selection - SSH config only
    print("\n[2] Specific leaf: SSH server configuration")
    print("-" * 40)
    filter2 = """
    <filter>
      <ssh xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-crypto-ssh-cfg">
        <server/>
      </ssh>
    </filter>
    """
    resp2 = session.get_config(source="running", filter=filter2)
    xml2 = etree.fromstring(str(resp2))
    ssh_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-crypto-ssh-cfg"
    ssh_data = xml2.find(f".//{{{ssh_ns}}}ssh")
    if ssh_data is not None:
        server = ssh_data.find(f"{{{ssh_ns}}}server")
        if server is not None:
            print("SSH server configuration:")
            print(etree.tostring(server, pretty_print=True).decode())
        else:
            print("SSH present but no server config found")
    else:
        print("SSH configuration not found")

    # FILTER 3: BGP configuration filter
    print("\n[3] BGP configuration via Cisco native model")
    print("-" * 40)
    filter3 = """
    <filter>
      <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"/>
    </filter>
    """
    resp3 = session.get_config(source="running", filter=filter3)
    xml3 = etree.fromstring(str(resp3))
    bgp_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"
    bgp_data = xml3.find(f".//{{{bgp_ns}}}bgp")
    if bgp_data is not None:
        instance = bgp_data.find(f"{{{bgp_ns}}}instance")
        if instance is not None:
            as_elem = instance.find(f"{{{bgp_ns}}}instance-as")
            if as_elem is not None and as_elem[0] is not None:
                asn = as_elem[0].text
                print(f"BGP ASN: {asn}")
    else:
        print("No BGP configuration found under Cisco model")
        # Try OpenConfig BGP
        print("Trying OpenConfig BGP model...")
        filter3b = """
        <filter>
          <network-instances xmlns="http://openconfig.net/yang/network-instance">
            <network-instance>
              <protocols>
                <protocol>
                  <bgp/>
                </protocol>
              </protocols>
            </network-instance>
          </network-instances>
        </filter>
        """
        resp3b = session.get_config(source="running", filter=filter3b)
        print(f"OpenConfig BGP response: {len(str(resp3b))} chars")

    # FILTER 4: Combined namespaces
    print("\n[4] Combined filter: hostname + domain")
    print("-" * 40)
    filter4 = """
    <filter>
      <hostname xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-cfg"/>
      <domain xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ip-domain-cfg">
        <vrf>
          <vrf-name>default</vrf-name>
        </vrf>
      </domain>
    </filter>
    """
    resp4 = session.get_config(source="running", filter=filter4)
    print(f"Combined filter response: {len(str(resp4))} chars")
    xml4 = etree.fromstring(str(resp4))
    host_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-cfg"
    host = xml4.find(f".//{{{host_ns}}}hostname")
    if host is not None:
        print(f"Hostname: {host.text}")

    print("\nKey takeaways:")
    print("  - Empty XML elements in filter = 'give me everything under this path'")
    print("  - Content in filter elements = 'match only if value equals this'")
    print("  - Multiple top-level elements are combined with logical OR")
    print("  - Always include the correct namespace on filter elements")
