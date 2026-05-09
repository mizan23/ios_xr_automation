# IOS XR Automation (Beginner Friendly)

This repo is a small lab toolkit for talking to a Cisco IOS XR device using:

- NETCONF (via Python `ncclient`)
- gNMI (via `gnmic` CLI)
- `.env` credentials so you do not hardcode passwords

If you are a vibe coder / beginner: think of this as **ready-made scripts** to test connectivity, pull config, and query interface data quickly.

---

## What each file does

### `config.py`
Central config loader.

What it does:
- Looks for `.env` in this folder first, then parent folder
- Loads env vars with `python-dotenv`
- Applies defaults for host/ports
- Validates required keys (`XR_USERNAME`, `XR_PASSWORD`)
- Returns a Python dict used by all scripts

This is the shared "brain" for credentials and connection settings.

### `simple_xr_automation.py`
Quick credential sanity check.

What it does:
- Loads config via `load_xr_config()`
- Prints host, ports, username
- Masks password in output
- Fails early with a clear error if `.env` keys are missing

Use this first when debugging setup.

### `ios_xr_automation.py`
Main NETCONF demo script.

What it does:
- Resolves hostname to IP
- Connects to IOS XR via NETCONF
- Pulls `running` config (`get_config(source="running")`)
- Prints payload size
- Prints a sample of server YANG capabilities
- Prints ready-to-run `gnmic` example commands

Use this when you want to verify full NETCONF access and basic model discovery.

### `ios_xr_interface_automation.py`
Interface-specific NETCONF query.

What it does:
- Connects to device via NETCONF
- Sends an OpenConfig XML filter for one interface (default `Loopback0`)
- Returns raw response XML as string
- In script mode, prints response size

Use this when you want focused interface data instead of full running config.

### `ios_xr_automation_env.py`
Backward-compatible entrypoint.

What it does:
- Imports functions from `ios_xr_automation.py`
- Runs the same NETCONF + gNMI example output flow

Use this only if you already reference this filename from old notes/scripts.

### `run.sh`
Convenience command runner.

What it does:
- Wraps common actions behind one command
- Uses `../xr_venv/bin/python` if available, otherwise `python3`
- Supports these commands:
  - `check` -> run credential check
  - `netconf` -> run NETCONF full config demo
  - `interface` -> run interface query demo
  - `gnmic` -> run `gnmic` with auto-loaded `.env` creds
  - `all` -> run check + netconf + interface
  - `?` / `help` -> show help
- For `gnmic`, if encoding is not provided, it auto-adds `--encoding JSON_IETF`
- `./run.sh cisco gnmic ?` maps to `gnmic --help`

---

## Required `.env` variables

Create a `.env` file in this directory:

```env
XR_USERNAME=your_username
XR_PASSWORD=your_password
```

Optional (defaults shown):

```env
XR_HOSTNAME=sandbox-iosxr-1.cisco.com
XR_NETCONF_PORT=830
XR_GNMI_PORT=57777
```

---

## Install and run

## 1) Python setup

```bash
python3 -m venv xr_venv
source xr_venv/bin/activate
pip install -r requirements.txt
```

## 2) Optional: install `gnmic`

```bash
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"
gnmic version
```

If command is not found after install:

```bash
export PATH="$PATH:$HOME/.local/bin"
```

## 3) Run commands

```bash
./run.sh cisco ?
./run.sh cisco check
./run.sh cisco netconf
./run.sh cisco interface
./run.sh cisco gnmic
./run.sh cisco gnmic get --path openconfig-interfaces:interfaces
./run.sh cisco gnmic --encoding ascii get --path "show version"
```

---

## Typical workflow (easy mode)

1. `./run.sh cisco check` -> verify `.env` is good
2. `./run.sh cisco netconf` -> confirm NETCONF login and data pull
3. `./run.sh cisco interface` -> test a focused query
4. `./run.sh cisco gnmic ...` -> test gNMI paths/CLI queries

---

## Troubleshooting

- `Missing required .env keys`  
  Add `XR_USERNAME` and `XR_PASSWORD` to `.env`.

- `gnmic is not installed or not in PATH`  
  Install `gnmic`, then verify with `gnmic version`.

- `unsupported get-request encoding: JSON`  
  Use `JSON_IETF` (the wrapper already defaults to this).

- Connection failures / timeout  
  Check VPN/network reachability, DNS resolution, firewall, and port access.

---

## Quick mental model

- `config.py` = load + validate credentials
- `simple_xr_automation.py` = preflight check
- `ios_xr_automation.py` = full NETCONF demo
- `ios_xr_interface_automation.py` = targeted interface query
- `run.sh` = one command launcher for everything

That is the whole project in one view.
