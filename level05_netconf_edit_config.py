#!/usr/bin/env python3
"""
LEVEL 5: NETCONF Edit-Config - Making Configuration Changes
=============================================================
Topics covered:
  - edit_config() with merge, replace, delete operations
  - Candidate datastore + commit workflow
  - Confirmed commit (auto-rollback safety)
  - Error handling for invalid configurations
  - Configuring interfaces, descriptions, IP addresses
  - Verifying changes after configuration
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 5: NETCONF Edit-Config (Configuration Changes)")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # We'll use Loopback199 since it already exists on this device
    # Operation 1: Change interface description (merge)
    print("\n[1] MERGE: Update Loopback199 description")
    print("-" * 40)
    merge_config = """
    <config>
      <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
        <interface-configuration>
          <active>Loopback199</active>
          <description>NETCONF Level 5 Demo - Automated Config</description>
        </interface-configuration>
      </interface-configurations>
    </config>
    """
    try:
        session.edit_config(target="candidate", config=merge_config)
        session.commit()
        print("Loopback199 description updated via MERGE")
    except Exception as e:
        session.discard_changes()
        print(f"Merge error: {e}")

    # Operation 2: Verify the change
    print("\n[2] VERIFY: Read back Loopback199")
    print("-" * 40)
    check_filter = """
    <filter>
      <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
        <interface-configuration>
          <active>Loopback199</active>
        </interface-configuration>
      </interface-configurations>
    </filter>
    """
    resp = session.get_config(source="running", filter=check_filter)
    xml = etree.fromstring(str(resp))
    ifmgr_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    desc = xml.find(f".//{{{ifmgr_ns}}}description")
    if desc is not None:
        print(f"Current description: {desc.text}")

    # Operation 3: Confirmed commit with auto-rollback (safety mechanism)
    print("\n[3] CONFIRMED COMMIT: Template change with auto-rollback")
    print("-" * 40)
    print("This would auto-rollback if not confirmed within timeout.")
    print("Skipping actual execution to avoid disrupting sandbox.")
    print("Usage pattern:")
    print("  session.edit_config(target='candidate', config=...)")
    print("  session.commit(confirmed=True, timeout='300')  # 5 min")
    print("  # Verify everything works...")
    print("  session.commit()  # Confirm within timeout")

    # Operation 4: REPLACE operation
    print("\n[4] REPLACE vs MERGE (conceptual)")
    print("-" * 40)
    print("MERGE: Adds or updates specified elements, leaves others untouched")
    print("REPLACE: Replaces entire target subtree with provided config")
    print("DELETE: Removes the specified configuration element")
    print()
    print("REPLACE example (not executed):")
    print("  session.edit_config(target='candidate', config=...,")
    print("                        default_operation='replace')")

    # Operation 5: Candidate datastore workflow
    print("\n[5] Candidate Datastore Workflow")
    print("-" * 40)
    print("1. edit_config(target='candidate', ...)  # Stage changes")
    print("2. validate('candidate')                   # Validate syntax")
    print("3. commit()                                # Activate")
    print("4. discard_changes()                       # Abort if needed")

    print("\nKey takeaways:")
    print("  - IOS XR supports candidate datastore for safe staged changes")
    print("  - Confirmed commit prevents lockout from bad configurations")
    print("  - MERGE is safest - only touches what you specify")
    print("  - Always verify changes after committing")
    print("  - discard_changes() on exception is critical for cleanup")
