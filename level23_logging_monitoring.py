#!/usr/bin/env python3
"""
LEVEL 23: Structured Logging & Monitoring Integration
========================================================
Topics covered:
  - Production-grade logging (rotating files, levels, structured output)
  - Metrics collection (Prometheus-style counters and gauges)
  - Health endpoints for monitoring systems
  - Audit trail for all network operations
  - Integration with ELK/Splunk/Datadog
"""
import socket
import time
import json
import logging
import logging.handlers
from contextlib import contextmanager
from datetime import datetime, timezone
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

# ---------------------------------------------------------------------------
# Production Logging Setup
# ---------------------------------------------------------------------------
def setup_logging():
    """Configure production-grade structured logging."""
    logger = logging.getLogger("xr_automation")
    logger.setLevel(logging.DEBUG)

    # Console handler (human-readable)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))

    # File handler (structured JSON for log aggregation)
    file_handler = logging.handlers.RotatingFileHandler(
        "xr_automation.log", maxBytes=1_000_000, backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            if hasattr(record, "duration_ms"):
                log_entry["duration_ms"] = record.duration_ms
            if hasattr(record, "operation"):
                log_entry["operation"] = record.operation
            if hasattr(record, "device"):
                log_entry["device"] = record.device
            if record.exc_info and record.exc_info[1]:
                log_entry["error"] = str(record.exc_info[1])
            return json.dumps(log_entry)

    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


log = setup_logging()

# ---------------------------------------------------------------------------
# Metrics Collector
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Simple metrics collector (Prometheus-style)."""

    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        self.operation_log = []

    def increment_counter(self, name, value=1, labels=None):
        key = f"{name}_{json.dumps(labels or {} )}"
        self.counters[key] = self.counters.get(key, 0) + value

    def set_gauge(self, name, value, labels=None):
        key = f"{name}_{json.dumps(labels or {} )}"
        self.gauges[key] = value

    def record_operation(self, op_name, duration_ms, status, size=0):
        self.operation_log.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "operation": op_name,
            "duration_ms": round(duration_ms, 1),
            "status": status,
            "size": size,
        })
        hist_key = f"op_duration_{op_name}"
        self.histograms.setdefault(hist_key, []).append(duration_ms)

    def export_prometheus(self):
        """Export in Prometheus text format."""
        lines = []
        for key, value in self.counters.items():
            name = key.split("_")[0]
            lines.append(f"# HELP xr_{name} Counter for {name}")
            lines.append(f"# TYPE xr_{name} counter")
            lines.append(f"xr_{name} {value}")
        for key, value in self.gauges.items():
            name = key.split("_")[0]
            lines.append(f"# HELP xr_{name} Gauge for {name}")
            lines.append(f"# TYPE xr_{name} gauge")
            lines.append(f"xr_{name} {value}")
        return "\n".join(lines) + "\n"

    def summary(self):
        """Print metrics summary."""
        print(f"\n  {'='*50}")
        print(f"  Metrics Summary")
        print(f"  {'='*50}")
        print(f"  Operations: {len(self.operation_log)}")
        if self.operation_log:
            durations = [o["duration_ms"] for o in self.operation_log]
            successes = sum(1 for o in self.operation_log if o["status"] == "success")
            print(f"  Success rate: {successes / len(self.operation_log) * 100:.0f}%")
            print(f"  Avg duration: {sum(durations) / len(durations):.1f}ms")
            print(f"  Min duration: {min(durations):.1f}ms")
            print(f"  Max duration: {max(durations):.1f}ms")

        print(f"\n  Recent operations:")
        for op in self.operation_log[-5:]:
            status_icon = "[OK]" if op["status"] == "success" else "[FAIL]"
            print(f"    {status_icon} {op['ts'][11:19]} {op['operation']:<30} "
                  f"{op['duration_ms']:>6.1f}ms {op['size']:>8}")

        total_data = sum(o["size"] for o in self.operation_log)
        print(f"\n  Total data transferred: {total_data:,} chars")


metrics = MetricsCollector()

# ---------------------------------------------------------------------------
# Operation wrappers with logging + metrics
# ---------------------------------------------------------------------------
@contextmanager
def logged_netconf(operation_name):
    """Context manager that logs and times NETCONF operations."""
    start = time.perf_counter()
    log.info(f"Starting: {operation_name}")
    session = None
    try:
        session = manager.connect(
            host=ip, port=cfg["netconf_port"],
            username=cfg["username"], password=cfg["password"],
            hostkey_verify=False, device_params={"name": "iosxr"},
            timeout=15,
        )
        log.info(f"NETCONF connected (session {session.session_id})")
        yield session
        duration = (time.perf_counter() - start) * 1000
        metrics.record_operation(operation_name, duration, "success")
        log.info(f"Completed: {operation_name} ({duration:.0f}ms)")
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        metrics.record_operation(operation_name, duration, "error")
        metrics.increment_counter("netconf_errors", labels={"op": operation_name})
        log.error(f"Failed: {operation_name} - {e}", exc_info=True)
        raise
    finally:
        if session and session.connected:
            session.close_session()
            metrics.increment_counter("netconf_sessions")


@contextmanager
def logged_gnmi(operation_name):
    """Context manager that logs and times gNMI operations."""
    start = time.perf_counter()
    log.info(f"Starting gNMI: {operation_name}")
    client = None
    try:
        client = gNMIclient(
            target=(ip, str(cfg["gnmi_port"])),
            username=cfg["username"], password=cfg["password"],
            insecure=True,
        )
        client.connect()
        log.info("gNMI connected")
        yield client
        duration = (time.perf_counter() - start) * 1000
        metrics.record_operation(operation_name, duration, "success")
        log.info(f"Completed gNMI: {operation_name} ({duration:.0f}ms)")
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        metrics.record_operation(operation_name, duration, "error")
        metrics.increment_counter("gnmi_errors", labels={"op": operation_name})
        log.error(f"Failed gNMI: {operation_name} - {e}", exc_info=True)
        raise
    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass
            metrics.increment_counter("gnmi_sessions")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
def health_check():
    """Comprehensive health check with metrics."""
    log.info("Running health check")
    health = {"status": "healthy", "checks": {}}

    # NETCONF check
    try:
        with logged_netconf("health_check_netconf") as session:
            caps = len(session.server_capabilities)
            health["checks"]["netconf"] = {"status": "ok", "capabilities": caps}
            metrics.set_gauge("netconf_capabilities", caps)
    except Exception as e:
        health["checks"]["netconf"] = {"status": "error", "error": str(e)[:80]}
        health["status"] = "degraded"

    # gNMI check
    try:
        with logged_gnmi("health_check_gnmi") as client:
            caps = client.capabilities()
            models = len(caps.get("supported_models", []))
            health["checks"]["gnmi"] = {"status": "ok", "models": models}
            metrics.set_gauge("gnmi_models", models)
    except Exception as e:
        health["checks"]["gnmi"] = {"status": "error", "error": str(e)[:80]}
        health["status"] = "degraded"

    return health


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------
def audit_log(operation, target, detail=""):
    """Write structured audit log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "target": target,
        "user": cfg["username"],
        "detail": detail,
    }
    with open("audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------
print("=" * 60)
print("LEVEL 23: Logging & Monitoring Integration")
print("=" * 60)

# Run health check
print("\n[1] Health Check with Structured Logging")
print("-" * 40)
health = health_check()
print(f"  Status: {health['status']}")
for check, details in health["checks"].items():
    status = details["status"]
    print(f"  {check}: {status}")
audit_log("health_check", cfg["hostname"], f"status={health['status']}")

# Collect interface data with logging
print("\n[2] Interface Collection with Logging")
print("-" * 40)
try:
    with logged_netconf("get_interfaces") as session:
        fltr = '<filter><interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"/></filter>'
        config = session.get_config(source="running", filter=fltr)
        size = len(str(config))
        metrics.set_gauge("config_size", size)
        print(f"  Collected: {size} chars")
        audit_log("get_config", cfg["hostname"], "interfaces")
except Exception as e:
    print(f"  Error: {e}")

try:
    with logged_gnmi("get_interfaces") as client:
        data = client.get(path=["interfaces"])
        size = len(str(data))
        print(f"  gNMI interfaces: {size} chars")
        audit_log("gnmi_get", cfg["hostname"], "interfaces")
except Exception as e:
    print(f"  gNMI Error: {e}")

# Display metrics
metrics.summary()

# Prometheus export
print(f"\n[3] Prometheus Metrics Export")
print("-" * 40)
prom_text = metrics.export_prometheus()
print(prom_text[:500])

print(f"\n[4] Log Files Generated")
print("-" * 40)
print(f"  JSON structured log: xr_automation.log")
print(f"  Audit trail: audit.log")

print("\nKey takeaways:")
print("  - Structured JSON logging enables log aggregation (ELK/Splunk)")
print("  - Rotating file handlers prevent disk exhaustion")
print("  - Metrics enable monitoring dashboards and alerting")
print("  - Audit trail provides compliance and forensics")
print("  - Context managers wrap operations with automatic logging/metrics")
print("  - Prometheus format enables integration with Grafana")
print("  - Always separate audit logs (immutable) from debug logs")
