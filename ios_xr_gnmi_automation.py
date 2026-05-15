#!/usr/bin/env python3
"""IOS XR gNMI automation using .env credentials and pygnmi."""

import socket
import sys
from pygnmi.client import gNMIclient
from config import load_xr_config


def gnmi_demo():
    cfg = load_xr_config()
    ip = socket.gethostbyname(cfg["hostname"])
    target = (ip, str(cfg["gnmi_port"]))
    print(f"Target: {cfg['hostname']} ({ip}):{cfg['gnmi_port']}", flush=True)

    with gNMIclient(
        target=target,
        username=cfg["username"],
        password=cfg["password"],
        insecure=True,
    ) as client:
        caps = client.capabilities()
        print(f"\nCapabilities ({len(caps)}):", flush=True)
        for c in caps:
            print(f"  {c}", flush=True)

        paths = {
            "interfaces": "interfaces",
            "network-instances": "network-instances",
        }
        for label, path in paths.items():
            print(f"\n--- gNMI Get: {label} ---", flush=True)
            try:
                data = client.get(path=[path])
                size = len(str(data))
                print(f"Response: {size} chars", flush=True)
                print(data, flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)


if __name__ == "__main__":
    print("IOS XR gNMI Automation", flush=True)
    print("=" * 40, flush=True)
    try:
        gnmi_demo()
    except Exception as exc:
        print(f"Error: {type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
