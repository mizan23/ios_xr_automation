#!/usr/bin/env python3
"""
LEVEL 19: gNMI Set — Configuration via gNMI
==============================================
Topics covered:
  - gNMI Set operations (update, replace, delete)
  - Configuring interfaces via gNMI
  - gNMI vs NETCONF for configuration changes
  - JSON-encoded configuration payloads
  - Transaction safety with gNMI Set
"""
import socket
from pygnmi.client import gNMIclient, gNMISetError
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])
target = (ip, str(cfg["gnmi_port"]))

print("=" * 60)
print("LEVEL 19: gNMI Set Operations (Configuration)")
print("=" * 60)

with gNMIclient(
    target=target,
    username=cfg["username"],
    password=cfg["password"],
    insecure=True,
) as client:

    # 1. gNMI Set overview
    print("[1] gNMI Set Operations")
    print("-" * 40)
    print("gNMI Set supports three operations:")
    print("  UPDATE  - Add/update specified paths (like NETCONF MERGE)")
    print("  REPLACE - Replace entire subtree (like NETCONF REPLACE)")
    print("  DELETE  - Remove specified paths (like NETCONF DELETE)")
    print()
    print("Set request structure:")
    print("  client.set(update=[...], replace=[...], delete=[...])")

    # 2. Read current state for Loopback199
    print("\n[2] Read Current Loopback199 State")
    print("-" * 40)
    try:
        data = client.get(path=["interfaces/interface[name=Loopback199]"])
        print(f"Loopback199 data: {len(str(data))} chars")
        notif = data["notification"][0]
        for update in notif["update"]:
            val = update["val"]
            if isinstance(val, dict) and "interface" in val:
                intf = val["interface"][0]
                desc = intf.get("state", {}).get("description", "")
                print(f"  Description: '{desc}'")
    except Exception as e:
        print(f"  Read error: {e}")

    # 3. gNMI Set - UPDATE operation (conceptual)
    print("\n[3] gNMI Set - UPDATE Pattern")
    print("-" * 40)
    print("Update description via gNMI:")
    update_config = {
        "description": "gNMI Set Demo - Level 19"
    }
    print(f"  Payload: {update_config}")
    print()
    print("  client.set(update=[")
    print("      ('interfaces/interface[name=Loopback199]/config/description',")
    print("       {'description': 'gNMI Set Demo - Level 19'})")
    print("  ])")
    print()
    print("In production, this would update Loopback199 description via gNMI.")

    # 4. gNMI Set - DELETE operation (conceptual)
    print("\n[4] gNMI Set - DELETE Pattern")
    print("-" * 40)
    print("Delete description via gNMI:")
    print("  client.set(delete=[")
    print("      'interfaces/interface[name=Loopback199]/config/description'")
    print("  ])")

    # 5. gNMI vs NETCONF for Config
    print("\n[5] gNMI vs NETCONF for Configuration")
    print("-" * 40)
    comparison = [
        ("Transport", "gRPC/HTTP2", "SSH/TCP"),
        ("Encoding", "Protobuf/JSON", "XML only"),
        ("Datastores", "Single (config+state)", "running, candidate, startup"),
        ("Validation", "Basic", "validate RPC + YANG schema"),
        ("Rollback", "Not built-in", "candidate+commit, confirmed-commit"),
        ("Best for config", "Simple updates, telemetry+config", "Complex config, transactions"),
    ]
    print(f"  {'Aspect':<15} {'gNMI':<25} {'NETCONF':<25}")
    print(f"  {'-'*65}")
    for aspect, gn, nc in comparison:
        print(f"  {aspect:<15} {gn:<25} {nc:<25}")

    # 6. Transaction safety
    print("\n[6] Transaction Safety with gNMI Set")
    print("-" * 40)
    print("Pattern for safe gNMI configuration:")
    print("""
    def safe_gnmi_set(client, updates, verify_path):
        \"""Update and verify via gNMI.\"""
        # 1. Read current state (pre-check)
        before = client.get(path=[verify_path])
        
        # 2. Apply change
        client.set(update=updates)
        
        # 3. Read new state (post-check)
        after = client.get(path=[verify_path])
        
        # 4. Verify
        if not verify(before, after, updates):
            # 5. Rollback (reverse the update)
            client.set(delete=[p for p, _ in updates])
            raise Exception("Verification failed, rolled back")
        
        return True
    """)

    print("\nKey takeaways:")
    print("  - gNMI Set supports same CRUD operations as NETCONF edit-config")
    print("  - UPDATE = merge, REPLACE = replace, DELETE = remove")
    print("  - gNMI uses paths instead of XML for configuration targeting")
    print("  - NETCONF is still preferred for complex configuration management")
    print("  - gNMI Set is ideal for simple, path-based configuration changes")
    print("  - Always verify after Set operations in production")
