#!/usr/bin/env python3
"""IOS XR interface automation using .env credentials."""

import socket

from ncclient import manager

from config import load_xr_config


def get_interface_info(interface_name: str = "Loopback0") -> str:
    cfg = load_xr_config()
    ip = socket.gethostbyname(cfg["hostname"])
    print(f"Connecting to {cfg['hostname']} ({ip})...")

    with manager.connect(
        host=ip,
        port=cfg["netconf_port"],
        username=cfg["username"],
        password=cfg["password"],
        hostkey_verify=False,
        device_params={"name": "iosxr"},
    ) as session:
        filter_xml = f"""
        <filter>
          <interfaces xmlns="http://openconfig.net/yang/interfaces">
            <interface>
              <name>{interface_name}</name>
            </interface>
          </interfaces>
        </filter>
        """
        return str(session.get(filter_xml))


if __name__ == "__main__":
    print("IOS XR Interface Automation")
    print("=" * 40)
    try:
        output = get_interface_info("Loopback0")
        print("Interface query completed.")
        print(f"Response size: {len(output)} chars")
    except Exception as exc:
        print(f"Error: {exc}")
