#!/usr/bin/env python3
"""
LEVEL 7: gNMI Subscribe - Streaming Telemetry
===============================================
Topics covered:
  - subscribe() for real-time telemetry data
  - ONCE vs STREAM vs POLL subscription modes
  - SAMPLE vs ON_CHANGE subscription triggers
  - Processing subscription responses iteratively
  - Use cases: CPU monitoring, interface counters, BGP state changes
"""
import socket
import time
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])
target = (ip, str(cfg["gnmi_port"]))

print("=" * 60)
print("LEVEL 7: gNMI Subscribe (Streaming Telemetry)")
print("=" * 60)

with gNMIclient(
    target=target,
    username=cfg["username"],
    password=cfg["password"],
    insecure=True,
) as client:

    # MODE 1: ONCE subscription - single poll
    print("[1] Subscribe Mode: ONCE")
    print("-" * 40)
    print("ONCE = single data dump, like get() but subscription format")
    try:
        sub = client.subscribe(subscribe={"subscribe": [
            {"path": "interfaces", "mode": "once"}
        ]})
        count = 0
        for response in sub:
            if "update" in response:
                updates = response["update"].get("update", [])
                count += len(updates)
        print(f"Responses received: {count}")
    except Exception as e:
        print(f"ONCE error: {e}")

    # MODE 2: SAMPLE subscription - periodic polling (5 second interval)
    print("\n[2] Subscribe Mode: SAMPLE (polling every 5s)")
    print("-" * 40)
    print("SAMPLE = periodic poll at fixed interval")
    print("Collecting 3 samples of interface state...")
    try:
        sub = client.subscribe(subscribe={
            "prefix": "",
            "subscription": [
                {
                    "path": "interfaces",
                    "mode": "sample",
                    "sample_interval": 5000000000,  # 5 seconds in nanoseconds
                    "heartbeat_interval": 0,
                }
            ],
            "mode": "stream",
            "encoding": "json_ietf",
        })
        sample_count = 0
        for response in sub:
            if "update" in response:
                sample_count += 1
                print(f"  Sample {sample_count}: {len(str(response))} chars")
                if sample_count >= 3:
                    break
        print(f"Collected {sample_count} samples")
    except Exception as e:
        print(f"SAMPLE error: {e}")

    # MODE 3: STREAM with ON_CHANGE target-defined (conceptual)
    print("\n[3] ON_CHANGE Mode (conceptual)")
    print("-" * 40)
    print("ON_CHANGE = push data only when state changes")
    print("Use cases:")
    print("  - Interface up/down transitions")
    print("  - BGP neighbor state changes")
    print("  - Route table modifications")
    print("  - ACL hit counter thresholds")
    print()
    print("ON_CHANGE example pattern:")
    print("  sub = client.subscribe(subscribe={")
    print("    'subscription': [{")
    print("      'path': 'network-instances',")
    print("      'mode': 'on_change',")
    print("      'heartbeat_interval': 30000000000  # 30s heartbeat")
    print("    }],")
    print("    'mode': 'stream'")
    print("  })")

    # MODE 4: Real interface counter monitoring
    print("\n[4] Live Demo: Interface counter monitoring")
    print("-" * 40)
    print("Tracking GigabitEthernet0/0/0/0 counters via SAMPLE")
    sub = client.subscribe(subscribe={
        "subscription": [
            {
                "path": "interfaces/interface[name=GigabitEthernet0/0/0/0]/state/counters",
                "mode": "sample",
                "sample_interval": 10000000000,  # 10 seconds
            }
        ],
        "mode": "stream",
        "encoding": "json_ietf",
    })

    prev_in = None
    sample_count = 0
    for response in sub:
        if hasattr(response, "update") and response.update:
            for upd in response.update.update:
                val = upd.val
                in_pkts = val.get("in-pkts") if isinstance(val, dict) else None
                out_pkts = val.get("out-pkts") if isinstance(val, dict) else None
                if in_pkts:
                    now = time.strftime("%H:%M:%S")
                    print(f"  [{now}] In: {in_pkts}, Out: {out_pkts}")
                    if prev_in:
                        delta = int(in_pkts) - int(prev_in)
                        print(f"         Delta: {delta} pkts")
                    prev_in = in_pkts
            sample_count += 1
            if sample_count >= 1:
                break

    print("\nKey takeaways:")
    print("  - SAMPLE mode = periodic polling (N second interval)")
    print("  - ON_CHANGE mode = push only on state changes (efficient)")
    print("  - heartbeat_interval ensures you know the session is alive")
    print("  - gNMI subscriptions enable real-time monitoring pipelines")
    print("  - Use with databases/TSDB for historical trending")
