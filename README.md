# IOS XR Automation Toolkit

> Beginner-friendly Python + shell toolkit for Cisco IOS XR labs using **NETCONF** and **gNMI**.

This project helps you quickly validate credentials, connect to IOS XR, pull running config, query interface data, and run `gnmic` commands with `.env` credentials.

## Why this repo exists

If you are learning network automation (or just want fast results), this repo gives you small scripts that are easy to read and easy to run.

- No hardcoded credentials
- No heavy framework
- Clear one-command workflow from `run.sh`

---

## Project map

| File | Purpose | When to use |
|---|---|---|
| `config.py` | Loads `.env`, applies defaults, validates required keys | Every script depends on this |
| `simple_xr_automation.py` | Credential sanity check | First run after editing `.env` |
| `ios_xr_automation.py` | Full NETCONF demo (`running` config + capabilities) | Verify end-to-end NETCONF access |
| `ios_xr_interface_automation.py` | NETCONF query for one interface (`Loopback0` default) | Pull targeted interface data |
| `ios_xr_automation_env.py` | Backward-compatible wrapper around `ios_xr_automation.py` | Keep old command compatibility |
| `run.sh` | Friendly command runner for all actions, including `gnmic` passthrough | Daily usage entrypoint |
| `requirements.txt` | Python dependencies | Install environment |

---

## What `run.sh` can do

```bash
./run.sh cisco ?
./run.sh cisco check
./run.sh cisco netconf
./run.sh cisco interface
./run.sh cisco gnmic
./run.sh cisco gnmic get --path openconfig-interfaces:interfaces
./run.sh cisco gnmic --encoding ascii get --path "show version"
./run.sh cisco all
```

### Notes

- `gnmic` arguments are passed through exactly after `gnmic`
- If no encoding is provided, wrapper adds `--encoding JSON_IETF`
- `./run.sh cisco gnmic ?` and `./run.sh cisco gnmic help` map to `gnmic --help`

---

## Environment variables

Create `.env` in the repo root:

```env
XR_USERNAME=your_username
XR_PASSWORD=your_password
```

Optional values (defaults shown):

```env
XR_HOSTNAME=sandbox-iosxr-1.cisco.com
XR_NETCONF_PORT=830
XR_GNMI_PORT=57777
```

---

## Quick start

### 1) Python environment

```bash
python3 -m venv xr_venv
source xr_venv/bin/activate
pip install -r requirements.txt
```

### 2) Install `gnmic` (optional but recommended)

```bash
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"
gnmic version
```

If `gnmic` is not found:

```bash
export PATH="$PATH:$HOME/.local/bin"
```

### 3) Run in this order

1. `./run.sh cisco check`
2. `./run.sh cisco netconf`
3. `./run.sh cisco interface`
4. `./run.sh cisco gnmic get --path openconfig-interfaces:interfaces`

---

## Script behavior details

### `config.py`

- Searches `.env` in current folder, then parent folder
- Loads variables via `python-dotenv`
- Requires `XR_USERNAME` and `XR_PASSWORD`
- Returns normalized config dict:
  - `hostname`, `username`, `password`, `netconf_port`, `gnmi_port`

### `simple_xr_automation.py`

- Calls `load_xr_config()`
- Prints resolved settings (password masked)
- Stops with a clear error if required keys are missing

### `ios_xr_automation.py`

- Resolves hostname to IP
- Opens NETCONF session via `ncclient.manager.connect(...)`
- Retrieves running config with `get_config(source="running")`
- Prints response size and sample YANG capabilities
- Prints suggested `gnmic` commands

### `ios_xr_interface_automation.py`

- Opens NETCONF session
- Sends XML filter for one interface (`Loopback0` by default)
- Returns raw XML response as string

### `ios_xr_automation_env.py`

- Compatibility entrypoint for old script names
- Reuses `netconf_example()` and `print_gnmi_examples()` from `ios_xr_automation.py`

---

## Troubleshooting

### `Missing required .env keys`

Add both keys to `.env`:

- `XR_USERNAME`
- `XR_PASSWORD`

### `gnmic is not installed or not in PATH`

- Install `gnmic`
- Verify with `gnmic version`
- Export path if needed: `export PATH="$PATH:$HOME/.local/bin"`

### `unsupported get-request encoding: JSON`

Your target does not accept plain JSON for that request.

- Use `--encoding JSON_IETF`
- `run.sh` already defaults to `JSON_IETF` if you do not provide one

### Connection timeout / auth failure

Check:

- DNS resolves hostname correctly
- VPN/network path to lab is up
- NETCONF/gNMI ports are reachable
- Username/password are correct

---

## Security notes

- `.env` is ignored by git (`.gitignore`)
- Do not paste real passwords into screenshots or issue trackers
- Prefer lab or sandbox credentials over production creds

---

## Mental model (one-minute recap)

- `config.py` = settings + validation
- `check` = preflight
- `netconf` = full config pull
- `interface` = focused data pull
- `gnmic` = telemetry/CLI-style queries
- `run.sh` = single front door for all of the above

If you can run `check`, `netconf`, and one `gnmic` query successfully, your lab automation foundation is in good shape.
