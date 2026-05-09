#!/usr/bin/env python3
import os
from pathlib import Path

from dotenv import load_dotenv


def load_xr_config():
    script_dir = Path(__file__).resolve().parent
    candidates = [script_dir / ".env", script_dir.parent / ".env"]
    for env_path in candidates:
        if env_path.exists():
            load_dotenv(env_path)
            break

    hostname = os.getenv("XR_HOSTNAME", "sandbox-iosxr-1.cisco.com")
    username = os.getenv("XR_USERNAME")
    password = os.getenv("XR_PASSWORD")
    netconf_port = int(os.getenv("XR_NETCONF_PORT", "830"))
    gnmi_port = int(os.getenv("XR_GNMI_PORT", "57777"))

    missing = [k for k, v in {
        "XR_USERNAME": username,
        "XR_PASSWORD": password,
    }.items() if not v]

    if missing:
        raise ValueError(f"Missing required .env keys: {', '.join(missing)}")

    return {
        "hostname": hostname,
        "username": username,
        "password": password,
        "netconf_port": netconf_port,
        "gnmi_port": gnmi_port,
    }
