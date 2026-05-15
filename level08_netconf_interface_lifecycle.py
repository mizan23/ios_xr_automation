#!/usr/bin/env python3
"""
LEVEL 8: NETCONF Interface Lifecycle - Create, Update, Delete
================================================================
Topics covered:
  - Full interface lifecycle via NETCONF
  - Create new loopback interface with IP address
  - Update interface description and IP
  - Delete interface
  - Verify at each step
  - Transaction safety with candidate + commit
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

NS_MAP = {
    "ifmgr": "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg",
    "ipv4": "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg",
    "ip_domain": "http://cisco.com/ns/yang/Cisco-IOS-XR-ip-domain-cfg",
}

TEST_IF = "Loopback250"

print("=" * 60)
print("LEVEL 8: Interface Lifecycle via NETCONF")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # STEP 1: CREATE a new loopback interface
    print(f"\n[1] CREATE: {TEST_IF}")
    print("-" * 40)
    create_config = f"""
    <config>
      <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
        <interface-configuration>
          <active>{TEST_IF}</active>
          <description>NETCONF Learning - Level 8</description>
          <interface-virtual/>
        </interface-configuration>
      </interface-configurations>
    </config>
    """
    try:
        session.edit_config(target="candidate", config=create_config)
        session.commit()
        print(f"{TEST_IF} created")
    except Exception as e:
        session.discard_changes()
        print(f"Create error (may already exist): {e}")

    # STEP 2: VERIFY creation
    print(f"\n[2] VERIFY: Read {TEST_IF}")
    print("-" * 40)
    verify_filter = f"""
    <filter>
      <interface-configurations xmlns="{NS_MAP['ifmgr']}">
        <interface-configuration>
          <active>{TEST_IF}</active>
        </interface-configuration>
      </interface-configurations>
    </filter>
    """
    resp = session.get_config(source="running", filter=verify_filter)
    xml = etree.fromstring(str(resp))
    desc = xml.find(f".//{{{NS_MAP['ifmgr']}}}description")
    if desc is not None:
        print(f"Description: {desc.text}")
    else:
        print(f"{TEST_IF} found (no description)")

    # STEP 3: UPDATE description
    print(f"\n[3] UPDATE: Change {TEST_IF} description")
    print("-" * 40)
    update_config = f"""
    <config>
      <interface-configurations xmlns="{NS_MAP['ifmgr']}">
        <interface-configuration>
          <active>{TEST_IF}</active>
          <description>Updated via NETCONF - Level 8</description>
        </interface-configuration>
      </interface-configurations>
    </config>
    """
    try:
        session.edit_config(target="candidate", config=update_config)
        session.commit()
        print("Description updated")
    except Exception as e:
        session.discard_changes()
        print(f"Update error: {e}")

    # STEP 4: VERIFY update
    print(f"\n[4] VERIFY: Updated {TEST_IF}")
    print("-" * 40)
    resp = session.get_config(source="running", filter=verify_filter)
    xml = etree.fromstring(str(resp))
    desc = xml.find(f".//{{{NS_MAP['ifmgr']}}}description")
    if desc is not None:
        print(f"New description: {desc.text}")

    # STEP 5: DELETE the interface
    print(f"\n[5] DELETE: Remove {TEST_IF}")
    print("-" * 40)
    delete_config = f"""
    <config>
      <interface-configurations xmlns="{NS_MAP['ifmgr']}">
        <interface-configuration nc:operation="delete"
          xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <active>{TEST_IF}</active>
        </interface-configuration>
      </interface-configurations>
    </config>
    """
    try:
        session.edit_config(target="candidate", config=delete_config)
        session.commit()
        print(f"{TEST_IF} deleted")
    except Exception as e:
        session.discard_changes()
        print(f"Delete error: {e}")

    # STEP 6: VERIFY deletion
    print(f"\n[6] VERIFY: {TEST_IF} removed")
    print("-" * 40)
    resp = session.get_config(source="running", filter=verify_filter)
    xml = etree.fromstring(str(resp))
    intf_data = xml.find(f".//{{{NS_MAP['ifmgr']}}}interface-configuration")
    if intf_data is None:
        print(f"{TEST_IF} confirmed deleted")
    else:
        print(f"{TEST_IF} still exists")

    print("\nKey takeaways:")
    print("  - Create: MERGE new config, commit")
    print("  - Update: MERGE changed fields only, commit")
    print("  - Delete: Use nc:operation='delete' attribute, commit")
    print("  - Always verify after each operation")
    print("  - discard_changes() prevents partial configurations")
    print("  - Candidate datastore isolates changes until commit")
