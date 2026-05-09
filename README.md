# IOS XR Automation Toolkit

> Beginner-friendly Python + shell toolkit for Cisco IOS XR labs using **NETCONF** and **gNMI**.

This project helps you quickly validate credentials, connect to IOS XR, pull running config, query interface data, and run `gnmic` commands with `.env` credentials.

## Table of contents

- [Why this repo exists](#why-this-repo-exists)
- [Project map](#project-map)
- [What runsh can do](#what-runsh-can-do)
- [Environment variables](#environment-variables)
- [Quick start](#quick-start)
- [Script behavior details](#script-behavior-details)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)
- [Mental model (one-minute recap)](#mental-model-one-minute-recap)
- [Deep dive: textbook-style explanation of every Python file](#deep-dive-textbook-style-explanation-of-every-python-file)
- [How all Python files work together (system view)](#how-all-python-files-work-together-system-view)
- [Suggested learning path (for CCNA/CCNP automation learners)](#suggested-learning-path-for-ccnaccnp-automation-learners)
- [Glossary (quick definitions)](#glossary-quick-definitions)

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

---

## Deep dive: textbook-style explanation of every Python file

This section explains each `.py` file in a teaching style: what problem it solves, how it works internally, what inputs it needs, what it returns/prints, and what to modify when you extend the project.

<details>
<summary><strong>1) config.py - configuration and credential layer</strong></summary>

### 1) `config.py` - configuration and credential layer

### Primary purpose

`config.py` is the configuration foundation of the project. Instead of scattering credentials and connection parameters across scripts, all runtime settings are loaded and validated in one place.

### Why this design matters

In automation, configuration drift causes many bugs (one script uses one hostname, another script uses another port). Centralizing config in one module gives:

- consistency across scripts,
- easier troubleshooting,
- safer credential handling,
- less duplicated code.

### Step-by-step internal flow

1. Determine script location using `Path(__file__).resolve().parent`.
2. Build two possible `.env` paths:
   - current directory `.env`
   - parent directory `.env`
3. Load the first `.env` file that exists.
4. Read env vars:
   - required: `XR_USERNAME`, `XR_PASSWORD`
   - optional: `XR_HOSTNAME`, `XR_NETCONF_PORT`, `XR_GNMI_PORT`
5. Apply defaults for optional values if missing.
6. Validate required values and raise a clear `ValueError` if missing.
7. Return a normalized Python dictionary used by all other scripts.

### Inputs

- Environment variables from `.env` and shell.

### Output

- Python dict with canonical keys:
  - `hostname`
  - `username`
  - `password`
  - `netconf_port`
  - `gnmi_port`

### Typical failure modes

- Missing `.env` keys -> `ValueError`
- Non-numeric port values -> `int(...)` conversion error

### Extension ideas

- Add `XR_TIMEOUT` with default timeout values.
- Add optional strict mode to reject default hostname usage.
- Add schema validation (`pydantic`) for stronger type checks.

---

</details>

<details>
<summary><strong>2) simple_xr_automation.py - preflight and sanity-check script</strong></summary>

### 2) `simple_xr_automation.py` - preflight and sanity-check script

### Primary purpose

This script is a lightweight preflight check. It verifies that configuration can be loaded before any network connection attempt.

### Why it exists

When beginners troubleshoot automation, they often mix credential errors with network errors. This script isolates config validation first, so you can quickly answer: "Are my credentials and variables loaded correctly?"

### Step-by-step internal flow

1. Print a clear header.
2. Call `load_xr_config()` from `config.py`.
3. If successful:
   - print hostname, NETCONF port, gNMI port, username,
   - print masked password marker.
4. If failure occurs:
   - catch exception,
   - print human-readable error.

### Inputs

- `.env` values through `config.py`.

### Output

- Console text only (no files written).

### What it does not do

- It does not open NETCONF/gNMI sessions.
- It does not validate live network reachability.

### Best use case

Run this first after editing `.env` or cloning on a new machine.

---

</details>

<details>
<summary><strong>3) ios_xr_automation.py - main NETCONF workflow demonstration</strong></summary>

### 3) `ios_xr_automation.py` - main NETCONF workflow demonstration

### Primary purpose

This is the core operational script. It demonstrates a complete NETCONF session lifecycle against IOS XR and gives practical gNMI command examples.

### Conceptual architecture

The script has two major functions:

- `netconf_example()` -> performs NETCONF operations.
- `print_gnmi_examples()` -> prints `gnmic` commands matching loaded config.

The `__main__` block orchestrates both.

### NETCONF flow in detail (`netconf_example()`)

1. Load settings via `load_xr_config()`.
2. Resolve DNS hostname to IPv4 via `socket.gethostbyname(...)`.
3. Build NETCONF connection with `ncclient.manager.connect(...)`:
   - host = resolved IP
   - port = `netconf_port`
   - username/password from config
   - `hostkey_verify=False`
   - `device_params={"name": "iosxr"}`
4. Request running configuration:
   - `session.get_config(source="running")`
5. Print payload length (quick signal of successful retrieval).
6. Iterate server capabilities and print selected model URIs.

### Why capability printing is useful

Capabilities reveal which YANG modules and revisions the server exposes. That helps you:

- pick valid models for future automation,
- confirm platform feature support,
- compare behavior across IOS XR versions.

### gNMI helper flow (`print_gnmi_examples()`)

1. Reload same config values.
2. Print command templates using current host/port/user.
3. Keep password masked in output to avoid accidental exposure in terminal logs.

### Inputs

- `.env` configuration
- reachable IOS XR endpoint

### Output

- Console output with NETCONF status, payload size, capabilities, and `gnmic` examples.

### What to extend next

- Save NETCONF XML output to a timestamped file.
- Add XML parsing for specific fields (hostname, interface count).
- Add command-line flags for host override and capability count.

---

</details>

<details>
<summary><strong>4) ios_xr_interface_automation.py - focused OpenConfig interface query</strong></summary>

### 4) `ios_xr_interface_automation.py` - focused OpenConfig interface query

### Primary purpose

This script narrows scope from "entire running config" to "single interface data" using an XML filter. It is designed for targeted, faster, and more relevant queries.

### Why filtered queries are important

In real environments, full configuration pulls are large and noisy. Filtered queries:

- reduce payload size,
- speed up troubleshooting,
- support feature-specific automation pipelines.

### Step-by-step internal flow

1. Function `get_interface_info(interface_name="Loopback0")` is called.
2. Load config and resolve hostname.
3. Open NETCONF session via `manager.connect(...)`.
4. Construct XML filter string using OpenConfig namespace:
   - `http://openconfig.net/yang/interfaces`
5. Inject requested interface name into filter.
6. Execute `session.get(filter_xml)`.
7. Return raw NETCONF response as string.
8. In script mode (`__main__`), call with `Loopback0`, print completion + response size.

### Inputs

- interface name (function parameter)
- `.env` connection values

### Output

- raw XML response string
- console status in direct script execution

### Design notes

- Current implementation uses direct string formatting in XML. This is fine for lab usage, but for production hardening you may sanitize/validate interface names.

### Extension ideas

- Add CLI argument parsing (`argparse`) for interface name.
- Parse response into structured JSON-like dict.
- Add fallback behavior when interface is absent.

---

</details>

<details>
<summary><strong>5) ios_xr_automation_env.py - compatibility and migration bridge</strong></summary>

### 5) `ios_xr_automation_env.py` - compatibility and migration bridge

### Primary purpose

This file provides a stable, backward-compatible entrypoint for users/scripts that still call the older filename.

### Why it exists

Renaming files in active projects can break:

- shell aliases,
- automation pipelines,
- documentation snippets,
- student notes/lab guides.

A compatibility wrapper reduces migration friction.

### Step-by-step internal flow

1. Import `netconf_example` and `print_gnmi_examples` from `ios_xr_automation.py`.
2. Define `main()` to print a mode-specific header.
3. Call imported functions in same order.
4. Catch and print exceptions identically.

### Inputs/outputs

- Same as `ios_xr_automation.py`.

### Practical guidance

- Keep this file while users transition.
- Deprecate later once all references are updated.

</details>

---

## How all Python files work together (system view)

Think in layers:

1. **Configuration layer**: `config.py`
2. **Validation/preflight layer**: `simple_xr_automation.py`
3. **Operational NETCONF layer**: `ios_xr_automation.py`
4. **Targeted query layer**: `ios_xr_interface_automation.py`
5. **Compatibility layer**: `ios_xr_automation_env.py`

Data path:

- `.env` -> `config.py` -> shared dict -> network scripts -> console output

---

## Suggested learning path (for CCNA/CCNP automation learners)

1. Read `config.py` first to understand environment loading and validation.
2. Run and inspect `simple_xr_automation.py` output.
3. Read `ios_xr_automation.py` and map each print line to an action.
4. Study the interface filter in `ios_xr_interface_automation.py`.
5. Modify one variable at a time (hostname, interface name, encoding) and observe behavior.

---

## Glossary (quick definitions)

- **NETCONF**: Network management protocol using XML over SSH.
- **gNMI**: gRPC Network Management Interface for telemetry/config operations.
- **YANG model**: Data model describing network configuration/state structure.
- **Capability URI**: Server-advertised model/version support string.
- **OpenConfig**: Vendor-neutral YANG model set.
- **Preflight check**: Early validation step before expensive operations.
