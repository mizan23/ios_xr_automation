#!/usr/bin/env python3
"""
LEVEL 11: gNMI Telemetry Pipeline with Data Processing
=========================================================
Topics covered:
  - Continuous telemetry collection loop
  - Data transformation (raw gNMI -> structured records)
  - JSON export for downstream consumption
  - Interface counter delta calculation (rate computation)
  - Timestamp normalization
  - Building a lightweight telemetry collector
"""
import socket
import json
import time
from datetime import datetime, timezone
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])
target = (ip, str(cfg["gnmi_port"]))

print("=" * 60)
print("LEVEL 11: gNMI Telemetry Pipeline")
print("=" * 60)


def collect_interface_state(client, path="interfaces"):
    """Collect full interface state snapshot."""
    data = client.get(path=[path])
    notif = data["notification"][0]
    timestamp = notif["timestamp"]
    records = []
    for update in notif["update"]:
        intf_list = update["val"].get("interface", [])
        for intf in intf_list:
            state = intf.get("state", {})
            counters = state.get("counters", {})
            record = {
                "timestamp": timestamp,
                "timestamp_iso": datetime.fromtimestamp(
                    timestamp / 1_000_000_000, tz=timezone.utc
                ).isoformat(),
                "name": intf["name"],
                "type": state.get("type", ""),
                "admin_status": state.get("admin-status", ""),
                "oper_status": state.get("oper-status", ""),
                "mtu": state.get("mtu", 0),
                "description": state.get("description", ""),
                "in_pkts": counters.get("in-pkts", "0"),
                "out_pkts": counters.get("out-pkts", "0"),
                "in_octets": counters.get("in-octets", "0"),
                "out_octets": counters.get("out-octets", "0"),
                "in_errors": counters.get("in-errors", "0"),
                "out_errors": counters.get("out-errors", "0"),
                "in_discards": counters.get("in-discards", "0"),
                "out_discards": counters.get("out-discards", "0"),
            }
            # IP addresses
            subs = intf.get("subinterfaces", {}).get("subinterface", [])
            for sub in subs:
                ipv4 = sub.get("openconfig-if-ip:ipv4", {})
                addrs = ipv4.get("addresses", {}).get("address", [])
                for addr in addrs:
                    record.setdefault("ip_addresses", []).append(
                        f"{addr['ip']}/{addr['state']['prefix-length']}"
                    )

            records.append(record)
    return records


def calculate_rates(prev_records, curr_records):
    """Calculate packet rates between two snapshots."""
    prev_map = {r["name"]: r for r in prev_records}
    rates = {}
    for curr in curr_records:
        name = curr["name"]
        prev = prev_map.get(name)
        if prev:
            delta_time = (curr["timestamp"] - prev["timestamp"]) / 1_000_000_000
            if delta_time > 0:
                rates[name] = {
                    "in_pps": (int(curr["in_pkts"]) - int(prev["in_pkts"])) / delta_time,
                    "out_pps": (int(curr["out_pkts"]) - int(prev["out_pkts"])) / delta_time,
                    "in_bps": (int(curr["in_octets"]) - int(prev["in_octets"])) * 8 / delta_time,
                    "out_bps": (int(curr["out_octets"]) - int(prev["out_octets"])) * 8 / delta_time,
                    "delta_s": delta_time,
                }
    return rates


with gNMIclient(
    target=target,
    username=cfg["username"], password=cfg["password"],
    insecure=True,
) as client:

    # Phase 1: Collect two snapshots with a gap
    print("[1] Collecting telemetry snapshots...")
    print("-" * 40)
    snap1 = collect_interface_state(client)
    print(f"Snapshot 1: {len(snap1)} interfaces at "
          f"{datetime.fromtimestamp(snap1[0]['timestamp'] / 1_000_000_000, tz=timezone.utc).strftime('%H:%M:%S')}")

    print("Waiting 10 seconds...")
    time.sleep(10)

    snap2 = collect_interface_state(client)
    print(f"Snapshot 2: {len(snap2)} interfaces at "
          f"{datetime.fromtimestamp(snap2[0]['timestamp'] / 1_000_000_000, tz=timezone.utc).strftime('%H:%M:%S')}")

    # Phase 2: Calculate rates
    print("\n[2] Interface Counter Rates")
    print("-" * 40)
    rates = calculate_rates(snap1, snap2)
    print(f"{'Interface':<30} {'In PPS':>10} {'Out PPS':>10} {'In Mbps':>10}")
    print("-" * 65)
    for name, rate in sorted(rates.items()):
        if rate["in_pps"] > 0 or rate["out_pps"] > 0:
            print(f"{name:<30} {rate['in_pps']:>10.1f} {rate['out_pps']:>10.1f} "
                  f"{rate['in_bps'] / 1_000_000:>10.2f}")

    # Phase 3: Export to JSON
    print("\n[3] Exporting data to JSON")
    print("-" * 40)
    export = {
        "device": cfg["hostname"],
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "interfaces": snap2,
        "rates": {k: {kk: round(vv, 2) if isinstance(vv, float) else vv
                      for kk, vv in v.items()}
                   for k, v in rates.items()},
    }
    filename = f"telemetry_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(export, f, indent=2)
    print(f"Exported to: {filename}")

    # Phase 4: System health via gNMI
    print("\n[4] System health snapshot")
    print("-" * 40)
    try:
        sys_data = client.get(path=["system"])
        sys_val = sys_data["notification"][0]["update"]
        if sys_val:
            print(f"System data: {len(str(sys_data))} chars")
    except Exception as e:
        print(f"System query: {e}")

    print("\nKey takeaways:")
    print("  - gNMI telemetry pipeline: Collect -> Transform -> Analyze -> Export")
    print("  - Counter deltas between snapshots give rates (pps, bps)")
    print("  - Timestamps in nanoseconds from gNMI; convert carefully")
    print("  - JSON export enables integration with monitoring systems")
    print("  - This pattern scales to 1000s of devices in production")
