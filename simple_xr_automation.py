#!/usr/bin/env python3
"""Quick check that .env credentials are available."""

from config import load_xr_config


def main() -> None:
    print("IOS XR Automation Credential Check")
    print("=" * 40)
    try:
        cfg = load_xr_config()
        print("Loaded .env successfully:")
        print(f"- Hostname: {cfg['hostname']}")
        print(f"- NETCONF Port: {cfg['netconf_port']}")
        print(f"- gNMI Port: {cfg['gnmi_port']}")
        print(f"- Username: {cfg['username']}")
        print("- Password: *****")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
