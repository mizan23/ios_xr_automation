#!/usr/bin/env python3
"""
LEVEL 21: Performance Benchmarking — NETCONF vs gNMI
=======================================================
Topics covered:
  - Latency comparison: NETCONF get-config vs gNMI get
  - Payload size comparison (XML vs JSON)
  - Throughput benchmarking
  - Connection establishment overhead
  - Statistical analysis (min/avg/max/stddev)
  - Protocol selection guidance based on use case
"""
import socket
import time
import statistics
from lxml import etree
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

ITERATIONS = 5

print("=" * 60)
print("LEVEL 21: Performance Benchmarking")
print("=" * 60)


def benchmark_netconf_get_config():
    """Benchmark NETCONF get_config latency."""
    times = []
    sizes = []
    for i in range(ITERATIONS):
        with manager.connect(
            host=ip, port=cfg["netconf_port"],
            username=cfg["username"], password=cfg["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=15,
        ) as session:
            start = time.perf_counter()
            config = session.get_config(source="running")
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # ms
            sizes.append(len(str(config)))
    return {
        "protocol": "NETCONF",
        "operation": "get_config(running)",
        "times_ms": times,
        "avg_ms": round(statistics.mean(times), 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
        "stdev_ms": round(statistics.stdev(times), 1) if len(times) > 1 else 0,
        "avg_size": round(statistics.mean(sizes)),
    }


def benchmark_netconf_get_interfaces():
    """Benchmark NETCONF filtered get_config."""
    fltr = '<filter><interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/></filter>'
    times = []
    sizes = []
    for _ in range(ITERATIONS):
        with manager.connect(
            host=ip, port=cfg["netconf_port"],
            username=cfg["username"], password=cfg["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=15,
        ) as session:
            start = time.perf_counter()
            config = session.get_config(source="running", filter=fltr)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
            sizes.append(len(str(config)))
    return {
        "protocol": "NETCONF",
        "operation": "get_config(interfaces filtered)",
        "times_ms": times,
        "avg_ms": round(statistics.mean(times), 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
        "stdev_ms": round(statistics.stdev(times), 1) if len(times) > 1 else 0,
        "avg_size": round(statistics.mean(sizes)),
    }


def benchmark_gnmi_get(path_name, path_value):
    """Benchmark gNMI get latency."""
    times = []
    sizes = []
    for _ in range(ITERATIONS):
        with gNMIclient(
            target=(ip, str(cfg["gnmi_port"])),
            username=cfg["username"], password=cfg["password"],
            insecure=True,
        ) as client:
            start = time.perf_counter()
            data = client.get(path=[path_value])
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
            sizes.append(len(str(data)))
    return {
        "protocol": "gNMI",
        "operation": f"get({path_name})",
        "times_ms": times,
        "avg_ms": round(statistics.mean(times), 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
        "stdev_ms": round(statistics.stdev(times), 1) if len(times) > 1 else 0,
        "avg_size": round(statistics.mean(sizes)),
    }


def benchmark_connection_establishment():
    """Benchmark connection setup time."""
    nc_times = []
    for _ in range(3):
        start = time.perf_counter()
        with manager.connect(
            host=ip, port=cfg["netconf_port"],
            username=cfg["username"], password=cfg["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=15,
        ) as session:
            pass
        nc_times.append((time.perf_counter() - start) * 1000)

    gn_times = []
    for _ in range(3):
        start = time.perf_counter()
        with gNMIclient(
            target=(ip, str(cfg["gnmi_port"])),
            username=cfg["username"], password=cfg["password"],
            insecure=True,
        ) as client:
            pass
        gn_times.append((time.perf_counter() - start) * 1000)

    return {
        "NETCONF connect": {
            "avg_ms": round(statistics.mean(nc_times), 1),
            "min_ms": round(min(nc_times), 1),
        },
        "gNMI connect": {
            "avg_ms": round(statistics.mean(gn_times), 1),
            "min_ms": round(min(gn_times), 1),
        },
    }


# --- Run benchmarks ---
print("\n[1] Running Benchmarks (this may take a minute)...")
print("-" * 40)

results = []

print("  NETCONF full config...")
results.append(benchmark_netconf_get_config())

print("  NETCONF filtered interfaces...")
results.append(benchmark_netconf_get_interfaces())

print("  gNMI interfaces...")
results.append(benchmark_gnmi_get("interfaces", "interfaces"))

print("  gNMI system...")
results.append(benchmark_gnmi_get("system", "system"))

print("  Connection establishment...")
conn_results = benchmark_connection_establishment()

# --- Display results ---
print("\n[2] Results Summary")
print("-" * 40)
print(f"{'Operation':<35} {'Avg(ms)':>8} {'Min(ms)':>8} {'Max(ms)':>8} {'Size(chars)':>12}")
print(f"{'-'*75}")
for r in results:
    print(f"{r['protocol']} {r['operation']:<25} "
          f"{r['avg_ms']:>8} {r['min_ms']:>8} {r['max_ms']:>8} {r['avg_size']:>12}")

print(f"\n[3] Connection Establishment")
print("-" * 40)
for proto, metrics in conn_results.items():
    print(f"  {proto}: avg {metrics['avg_ms']}ms, min {metrics['min_ms']}ms")

# --- Analysis ---
print("\n[4] Analysis & Recommendations")
print("-" * 40)
if results:
    nc_full = results[0]
    nc_filt = results[1]
    gn_if = results[2]

    print(f"  Full config (NETCONF): {nc_full['avg_ms']}ms avg, {nc_full['avg_size']} chars")
    print(f"  Filtered (NETCONF): {nc_filt['avg_ms']}ms avg, {nc_filt['avg_size']} chars")
    print(f"  gNMI interfaces: {gn_if['avg_ms']}ms avg, {gn_if['avg_size']} chars")

    size_reduction = (1 - nc_filt["avg_size"] / nc_full["avg_size"]) * 100
    print(f"\n  Filtering reduced payload by {size_reduction:.0f}%")

print("\n  Protocol selection guide:")
print("  ┌──────────────┬──────────────────────┬──────────────────────┐")
print("  │ Use Case     │ Recommended          │ Reason               │")
print("  ├──────────────┼──────────────────────┼──────────────────────┤")
print("  │ Full config  │ NETCONF              │ Candidate datastore  │")
print("  │ State data   │ gNMI                 │ Faster, JSON output  │")
print("  │ Telemetry    │ gNMI subscribe       │ Streaming native     │")
print("  │ Config deploy│ NETCONF              │ Transactions/rollback│")
print("  │ Quick health │ gNMI get             │ Low latency          │")
print("  │ DevOps/CI    │ RESTCONF/gNMI        │ JSON, web-friendly   │")
print("  └──────────────┴──────────────────────┴──────────────────────┘")

print("\nKey takeaways:")
print("  - Benchmark your specific device — results vary by hardware/version")
print("  - Filtered queries dramatically reduce payload and latency")
print("  - gNMI typically faster for state queries; NETCONF better for config")
print("  - Connection establishment overhead matters for frequent short sessions")
print("  - Use persistent sessions for high-frequency operations")
