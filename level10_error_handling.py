#!/usr/bin/env python3
"""
LEVEL 10: Robust Error Handling & Retry Logic
================================================
Topics covered:
  - Connection retry with exponential backoff
  - Timeout handling for NETCONF and gNMI
  - Graceful degradation when services are unavailable
  - Structured exception hierarchy
  - Logging instead of print() for production
  - Context manager lifecycle safety
"""
import socket
import time
import logging
from ncclient import manager
from ncclient.transport import SSHError, AuthenticationError
from pygnmi.client import gNMIclient
from config import load_xr_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 10: Error Handling & Retry Logic")
print("=" * 60)


def netconf_connect_with_retry(max_retries=3, base_delay=2):
    """Connect to NETCONF with exponential backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"NETCONF attempt {attempt}/{max_retries}")
            session = manager.connect(
                host=ip, port=cfg["netconf_port"],
                username=cfg["username"], password=cfg["password"],
                hostkey_verify=False, device_params={"name": "iosxr"},
                timeout=15,
            )
            log.info(f"NETCONF connected (session: {session.session_id})")
            return session
        except AuthenticationError as e:
            log.error(f"Authentication failed: {e}")
            raise  # Don't retry auth failures
        except SSHError as e:
            log.warning(f"SSH error: {e}")
            if attempt < max_retries:
                delay = base_delay ** attempt
                log.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
        except Exception as e:
            log.warning(f"Connection error: {type(e).__name__}: {e}")
            if attempt < max_retries:
                delay = base_delay ** attempt
                log.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
    return None


def gnmi_connect_with_retry(max_retries=3, base_delay=2):
    """Connect to gNMI with exponential backoff retry."""
    target = (ip, str(cfg["gnmi_port"]))
    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"gNMI attempt {attempt}/{max_retries}")
            client = gNMIclient(
                target=target,
                username=cfg["username"], password=cfg["password"],
                insecure=True,
            )
            client.connect()
            log.info("gNMI connected")
            return client
        except Exception as e:
            log.warning(f"gNMI error: {type(e).__name__}: {e}")
            if attempt < max_retries:
                delay = base_delay ** attempt
                log.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
    return None


def safe_netconf_get(session, filter_str=None, source="running"):
    """Safely execute NETCONF get with timeout and error handling."""
    try:
        if filter_str:
            return session.get_config(source=source, filter=filter_str)
        else:
            return session.get_config(source=source)
    except Exception as e:
        log.error(f"NETCONF get failed: {type(e).__name__}: {e}")
        return None


def safe_gnmi_get(client, paths):
    """Safely execute gNMI get with individual path error handling."""
    results = {}
    for path in paths:
        try:
            data = client.get(path=[path])
            results[path] = data
            log.info(f"gNMI get {path}: {len(str(data))} chars")
        except Exception as e:
            log.warning(f"gNMI get {path} failed: {e}")
            results[path] = None
    return results


# --- Demonstration ---
print("\n[1] Retry Pattern Demonstration")
print("-" * 40)
try:
    nc = netconf_connect_with_retry(max_retries=2, base_delay=1)
    if nc:
        print(f"NETCONF session: {nc.session_id}")
except Exception as e:
    print(f"NETCONF unavailable: {e}")

print("\n[2] Graceful Degradation: Try gNMI if NETCONF fails")
print("-" * 40)
try:
    gc = gnmi_connect_with_retry(max_retries=2, base_delay=1)
    if gc:
        caps = gc.capabilities()
        print(f"gNMI models: {len(caps.get('supported_models', []))}")
        gc.close()
except Exception as e:
    print(f"gNMI unavailable: {e}")

print("\n[3] Structured Error Types")
print("-" * 40)
print("Exception hierarchy for network automation:")
print("  ConnectionError - Base for all connectivity issues")
print("    SSHError - SSH transport failures")
print("    AuthenticationError - Bad credentials")
print("    TimeoutError - Operation exceeded deadline")
print("  RPCError - NETCONF RPC layer errors")
print("    BadValue - Invalid configuration value")
print("    MissingElement - Required field not provided")
print("  GrpcError - gNMI/gRPC layer errors")
print("    Unavailable - Service not reachable")
print("    NotFound - Requested path doesn't exist")

print("\n[4] Retry Strategy Patterns")
print("-" * 40)
print("Exponential backoff: delay = base_delay ^ attempt")
print("  Attempt 1: immediate")
print("  Attempt 2: 2s delay")
print("  Attempt 3: 4s delay")
print("  Attempt 4: 8s delay")
print()
print("Jitter: Add random 0-25% to avoid thundering herd")
print("Circuit breaker: Stop retrying after N consecutive failures")
print("Deadline: Absolute timeout regardless of retries")

print("\nKey takeaways:")
print("  - Never retry authentication failures")
print("  - Always set timeouts on network operations")
print("  - Use exponential backoff with jitter for retries")
print("  - Log all errors with context (host, operation, duration)")
print("  - Design for graceful degradation when services are down")

if nc and nc.connected:
    nc.close_session()
