#!/usr/bin/env python3
"""Backward-compatible entrypoint; same behavior as ios_xr_automation.py."""

from ios_xr_automation import netconf_example, print_gnmi_examples


def main() -> None:
    print("IOS XR Automation (.env mode)")
    print("=" * 40)
    try:
        netconf_example()
        print_gnmi_examples()
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
