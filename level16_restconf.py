#!/usr/bin/env python3
"""
LEVEL 16: RESTCONF — HTTP-based Network Automation
=====================================================
Topics covered:
  - RESTCONF vs NETCONF: architectural differences
  - HTTP methods: GET, POST, PUT, PATCH, DELETE
  - RESTCONF URL structure and resource paths
  - JSON/XML encoding in RESTCONF
  - Authentication (Basic Auth, token-based)
  - When to use RESTCONF over NETCONF
  - Building RESTCONF clients with Python requests
"""
import socket
import requests
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

RESTCONF_PORT = 443  # Standard HTTPS port for RESTCONF

print("=" * 60)
print("LEVEL 16: RESTCONF Protocol Introduction")
print("=" * 60)

print(f"\nDevice: {cfg['hostname']} ({ip})")
print(f"RESTCONF typically on port {RESTCONF_PORT} (HTTPS)")
print()

# 1. Architecture comparison
print("[1] NETCONF vs RESTCONF Architecture")
print("-" * 40)
comparison = [
    ("Transport", "SSH (TCP/830)", "HTTPS (TCP/443)"),
    ("Encoding", "XML only", "XML or JSON"),
    ("Operations", "get, get-config, edit-config, etc.", "GET, POST, PUT, PATCH, DELETE"),
    ("API Style", "RPC-based", "RESTful (resource-oriented)"),
    ("Discovery", "NETCONF capabilities", "YANG library + OpenAPI"),
    ("Best for", "Network engineers, CLI background", "Web developers, DevOps"),
    ("Tooling", "ncclient, netconf-console", "curl, requests, Postman"),
]
print(f"  {'Aspect':<15} {'NETCONF':<25} {'RESTCONF':<25}")
print(f"  {'-'*65}")
for aspect, nc, rc in comparison:
    print(f"  {aspect:<15} {nc:<25} {rc:<25}")

# 2. RESTCONF URL Structure
print("\n[2] RESTCONF URL Structure")
print("-" * 40)
print("Base URL: https://<device>/restconf/data/<module>:<container>")
print()
print("Example URLs:")
examples = [
    ("GET interfaces", "GET /restconf/data/ietf-interfaces:interfaces"),
    ("GET specific interface", "GET /restconf/data/ietf-interfaces:interfaces/interface=Loopback0"),
    ("GET OpenConfig BGP", "GET /restconf/data/openconfig-network-instance:network-instances"),
    ("GET operational state", "GET /restconf/data/ietf-interfaces:interfaces-state"),
    ("PATCH config", "PATCH /restconf/data/ietf-interfaces:interfaces/interface=Loopback99"),
]
for label, url in examples:
    print(f"  {label:<25} {url}")

# 3. RESTCONF Client Implementation
print("\n[3] RESTCONF Client (Python requests)")
print("-" * 40)

class RestconfClient:
    """Minimal RESTCONF client for IOS XR."""

    def __init__(self, host, port, username, password):
        self.base_url = f"https://{host}:{port}/restconf"
        self.auth = (username, password)
        self.headers = {
            "Accept": "application/yang-data+json",
            "Content-Type": "application/yang-data+json",
        }

    def get(self, path):
        """GET request to RESTCONF."""
        url = f"{self.base_url}/data/{path}"
        try:
            resp = requests.get(
                url, auth=self.auth, headers=self.headers,
                verify=False, timeout=10,
            )
            return resp.status_code, resp.json() if resp.ok else resp.text
        except Exception as e:
            return None, str(e)

    def patch(self, path, data):
        """PATCH request (merge configuration)."""
        url = f"{self.base_url}/data/{path}"
        try:
            resp = requests.patch(
                url, auth=self.auth, headers=self.headers,
                json=data, verify=False, timeout=10,
            )
            return resp.status_code, resp.text
        except Exception as e:
            return None, str(e)

# Try RESTCONF connectivity
print("Testing RESTCONF on port 443...")
try:
    rc = RestconfClient(ip, RESTCONF_PORT, cfg["username"], cfg["password"])
    status, result = rc.get("ietf-interfaces:interfaces")
    if status and status < 500:
        print(f"  Status: {status}")
        if isinstance(result, dict):
            print(f"  Response keys: {list(result.keys())[:5]}")
        else:
            print(f"  Response: {str(result)[:200]}")
    else:
        print(f"  RESTCONF not reachable on port {RESTCONF_PORT}")
        print("  (Many sandboxes don't expose RESTCONF HTTPS)")

    # Try port 8080 (common alternative)
    print(f"\nTesting RESTCONF on port 8080...")
    rc2 = RestconfClient(ip, 8080, cfg["username"], cfg["password"])
    status2, result2 = rc2.get("ietf-interfaces:interfaces")
    if status2 and status2 < 500:
        print(f"  Status: {status2}")
    else:
        print(f"  RESTCONF not available (sandbox limitation)")
except Exception as e:
    print(f"  RESTCONF test: {e}")

# 4. RESTCONF Operations Cheat Sheet
print("\n[4] RESTCONF Operations Cheat Sheet")
print("-" * 40)
ops = [
    ("GET", "Read data", "/restconf/data/<path>", 200),
    ("POST", "Create resource", "/restconf/data/<parent>", 201),
    ("PUT", "Replace resource", "/restconf/data/<path>", 200 or 204),
    ("PATCH", "Merge/update", "/restconf/data/<path>", 200 or 204),
    ("DELETE", "Remove resource", "/restconf/data/<path>", 204),
    ("OPTIONS", "Discover methods", "/restconf/data/<path>", 200),
]
for method, desc, url, ok_code in ops:
    print(f"  {method:<8} {desc:<18} → {url} ({ok_code})")

print("\nKey takeaways:")
print("  - RESTCONF = YANG-modeled data over REST/HTTP")
print("  - JSON support makes it ideal for web/DevOps integration")
print("  - Same YANG models as NETCONF, different transport")
print("  - Use PATCH (not PUT) for partial config updates")
print("  - requests library provides Python-native HTTP client")
print("  - Sandbox environments may not expose RESTCONF (use NETCONF/gNMI instead)")
