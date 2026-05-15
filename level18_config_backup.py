#!/usr/bin/env python3
"""
LEVEL 18: Configuration Backup, Restore & Diff
=================================================
Topics covered:
  - Full configuration backup to file
  - Incremental vs full backups
  - Configuration diff between versions
  - Restore from backup (candidate + commit workflow)
  - Git integration for config version control
  - Automated backup scheduling pattern
"""
import socket
import difflib
import time
import json
from datetime import datetime, timezone
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

BACKUP_DIR = "config_backups"

print("=" * 60)
print("LEVEL 18: Config Backup, Restore & Diff")
print("=" * 60)


def get_running_config(session):
    """Get the full running configuration."""
    return str(session.get_config(source="running"))


def backup_config(session, label=""):
    """Save running config to a timestamped backup file."""
    import os
    os.makedirs(BACKUP_DIR, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = f"backup_{ts}"
    if label:
        name += f"_{label}"

    config = get_running_config(session)
    path = f"{BACKUP_DIR}/{name}.xml"
    with open(path, "w") as f:
        f.write(config)

    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": cfg["hostname"],
        "size_bytes": len(config),
        "label": label,
    }
    with open(f"{BACKUP_DIR}/{name}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return path, config


def diff_configs(old_xml, new_xml, old_label="old", new_label="new"):
    """Generate a human-readable diff between two config versions."""
    old_lines = old_xml.splitlines(keepends=True)
    new_lines = new_xml.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"config_{old_label}",
        tofile=f"config_{new_label}",
    )
    return "".join(diff)


def extract_interface_configs(xml_str):
    """Extract interface configs for targeted comparison."""
    xml = etree.fromstring(xml_str)
    ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
    interfaces = {}
    for intf in xml.findall(f".//{{{ns}}}interface-configuration"):
        name_elem = intf.find(f"{{{ns}}}interface-name")
        if name_elem is not None:
            name = name_elem.text
            interfaces[name] = etree.tostring(intf, pretty_print=True).decode()
    return interfaces


with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # 1. Full configuration backup
    print("\n[1] Configuration Backup")
    print("-" * 40)
    path1, config1 = backup_config(session, label="baseline")
    print(f"Baseline backup: {path1}")
    print(f"Config size: {len(config1)} chars")

    # Extract interface configs
    ifaces1 = extract_interface_configs(config1)
    print(f"Interfaces in backup: {len(ifaces1)}")
    for name in sorted(ifaces1.keys())[:8]:
        print(f"  - {name}")

    # 2. Create a small change (via gNMI or conceptual)
    print("\n[2] Simulating Configuration Change")
    print("-" * 40)
    print("(In production, this would be done via NETCONF edit-config)")
    print("Generating diff demonstration...")

    # Create a modified version for diff demo
    modified = config1.replace("Loopback", "Loopback_MODIFIED_DEMO")

    diff = diff_configs(config1, modified, "baseline", "modified")
    changed_lines = [l for l in diff.splitlines() if l.startswith(("+", "-")) \
                     and not l.startswith(("+++", "---"))]
    print(f"Diff lines changed: {len(changed_lines)}")
    for line in changed_lines[:10]:
        print(f"  {line}")

    # 3. Restore pattern
    print("\n[3] Configuration Restore Pattern")
    print("-" * 40)
    print("Restore workflow:")
    print("  1. Load backup XML from file")
    print("  2. session.edit_config(target='candidate', config=backup_xml)")
    print("  3. session.validate('candidate')")
    print("  4. session.commit()  # or commit(confirmed=True) for safety")
    print()
    print("Rollback pattern:")
    print("  - IOS XR supports 'rollback-on-error' capability")
    print("  - If commit fails, device automatically discards candidate")
    print("  - Confirmed commit gives N-second window to verify")

    # 4. Targeted interface backup
    print("\n[4] Targeted Interface Backup")
    print("-" * 40)
    for name, config_xml in sorted(ifaces1.items())[:5]:
        safe_name = name.replace("/", "_")
        iface_path = f"{BACKUP_DIR}/interface_{safe_name}.xml"
        with open(iface_path, "w") as f:
            f.write(config_xml)
        print(f"  {name}: {iface_path} ({len(config_xml)} chars)")

    # 5. Backup scheduling pattern
    print("\n[5] Automated Backup Scheduling")
    print("-" * 40)
    print("Daily backup pattern:")
    print("""
    import schedule

    def daily_backup():
        with netconf_connect() as session:
            path, config = backup_config(session)
            old_backups = sorted(glob('config_backups/*.xml'))
            if len(old_backups) > 7:  # Keep 7 days
                for old in old_backups[:-7]:
                    os.remove(old)

    schedule.every().day.at("02:00").do(daily_backup)

    while True:
        schedule.run_pending()
        time.sleep(60)
    """)

    # 6. Git integration concept
    print("\n[6] Git-Based Configuration Version Control")
    print("-" * 40)
    print("Conceptual workflow:")
    print("  - Each backup commit to git repo")
    print("  - git diff shows changes between versions")
    print("  - git blame shows who changed what, when")
    print("  - Git tags mark approved/known-good configurations")
    print("  - CI/CD pipeline can validate configs before deploy")

    print("\nKey takeaways:")
    print("  - Regular config backups are essential for disaster recovery")
    print("  - Unified diffs reveal exactly what changed between backups")
    print("  - Interface-level backups enable granular restore")
    print("  - Confirmed commit provides safety window during restore")
    print("  - Git integration brings audit trail and version control")
    print("  - Production systems should backup pre- and post-change")
