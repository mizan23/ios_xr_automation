#!/usr/bin/env python3
"""
LEVEL 15: NETCONF Notifications — Real-time Event Streaming
==============================================================
Topics covered:
  - NETCONF notification subscriptions (RFC 5277)
  - create_subscription() for event streams
  - Processing NETCONF, SNMP, and Syslog notification types
  - Event-driven automation (react to config changes)
  - Notification filtering
  - Integration with gNMI telemetry for dual-protocol event handling
"""
import socket
import time
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 15: NETCONF Notifications (Event Streaming)")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # 1. Check notification capability
    print("\n[1] Notification Capability Check")
    print("-" * 40)
    caps = session.server_capabilities
    has_notif = any("notification" in c for c in caps)
    has_interleave = any("interleave" in c for c in caps)
    print(f"Notification support: {has_notif}")
    print(f"Interleave support: {has_interleave}")

    # 2. List available notification streams (IOS XR specific)
    print("\n[2] Available Notification Streams")
    print("-" * 40)
    streams = [
        "NETCONF",        # NETCONF config change events
        "SNMP",           # SNMP traps as NETCONF notifications
        "syslog",         # Syslog messages as notifications
        "all",            # All streams combined
    ]
    print("Typical IOS XR streams:")
    for stream in streams:
        print(f"  - {stream}")

    # 3. Create subscription demo (conceptual + practical)
    print("\n[3] Notification Subscription Pattern")
    print("-" * 40)
    print("Subscription flow:")
    print("  1. session.create_subscription(stream_name='NETCONF')")
    print("  2. Loop: notification = session.take_notification()")
    print("  3. Parse notification XML, extract event details")
    print("  4. React: trigger remediation, logging, alerting")

    # 4. Try actual subscription for a few notifications
    print("\n[4] Collecting NETCONF notifications (5 second window)")
    print("-" * 40)
    try:
        session.create_subscription(stream_name="NETCONF")
        print("Subscription created. Waiting for events...")

        notifications = []
        start = time.time()
        while time.time() - start < 5:
            try:
                notif = session.take_notification(block=False, timeout=2)
                if notif:
                    notifications.append(notif)
                    xml = etree.fromstring(notif.notification_xml)
                    event_time = xml.find(".//{urn:ietf:params:xml:ns:netconf:notification:1.0}eventTime")
                    event_elem = xml.find(".//{*}edit-config" if True else ".//{*}config-change")
                    if event_time is not None:
                        print(f"  [{event_time.text[:19]}] Event received")
            except Exception:
                time.sleep(0.5)

        print(f"Collected {len(notifications)} notifications in 5s")
    except Exception as e:
        print(f"Notification error (expected if no events): {e}")

    # 5. Notification-driven automation pattern
    print("\n[5] Event-Driven Automation Architecture")
    print("-" * 40)
    print("""
    Notification → Parser → Rule Engine → Action
    ─────────────────────────────────────────────
    config-change  → Extract path  → If bgp → Check peers
    syslog-CRITICAL → Parse message → If DOWN → Remediate
    snmp-trap      → Decode OID    → If threshold → Alert

    Implementation pattern:
    ```python
    while True:
        notif = session.take_notification(timeout=30)
        event = parse_notification(notif)
        for rule in rules:
            if rule.matches(event):
                rule.execute(event)
    ```
    """)

    print("\nKey takeaways:")
    print("  - NETCONF notifications enable event-driven network automation")
    print("  - create_subscription() + take_notification() form the event loop")
    print("  - Interleave capability allows operations while subscribed")
    print("  - Combine with gNMI ON_CHANGE for dual-protocol event coverage")
    print("  - Notification filtering reduces noise in production")
