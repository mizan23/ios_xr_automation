#!/usr/bin/env python3
"""IOS XR NETCONF automation using .env credentials."""

import socket

from ncclient import manager

from config import load_xr_config


def netconf_example() -> None:
    cfg = load_xr_config()
    ip = socket.gethostbyname(cfg["hostname"])
    print(f"Connecting to {cfg['hostname']} ({ip}) via NETCONF...")

    with manager.connect(
        host=ip,
        port=cfg["netconf_port"],
        username=cfg["username"],
        password=cfg["password"],
        hostkey_verify=False,
        device_params={"name": "iosxr"},
    ) as session:
        config = session.get_config(source="running")
        print("Running config retrieved.")
        print(f"Config payload size: {len(str(config))} chars")

        print("Sample server capabilities:")
        shown = 0
        for capability in session.server_capabilities:
            if "openconfig" in capability or "cisco" in capability:
                print(f"  - {capability}")
                shown += 1
            if shown >= 5:
                break


def print_gnmi_examples() -> None:
    cfg = load_xr_config()
    print("\ngNMI examples:")
    print(
        f"gnmic --address {cfg['hostname']}:{cfg['gnmi_port']} "
        f"--username {cfg['username']} --password '*****' "
        "--encoding JSON_IETF --insecure get --path \"openconfig-interfaces:interfaces\""
    )
    print(
        f"gnmic --address {cfg['hostname']}:{cfg['gnmi_port']} "
        f"--username {cfg['username']} --password '*****' "
        "--encoding ascii --insecure get --path \"show version\""
    )


if __name__ == "__main__":
    print("IOS XR Automation")
    print("=" * 40)
    try:
        netconf_example()
        print_gnmi_examples()
    except Exception as exc:
        print(f"Error: {exc}")
