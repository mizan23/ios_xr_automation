#!/usr/bin/env bash
set -euo pipefail

show_help() {
  echo "Cisco XR Automation Runner"
  echo
  echo "Usage:"
  echo "  ./run.sh cisco ?          Show commands"
  echo "  ./run.sh cisco check      Check .env credentials"
  echo "  ./run.sh cisco netconf    Run NETCONF example"
  echo "  ./run.sh cisco interface  Run interface query example"
  echo "  ./run.sh cisco gnmic ...  Run gnmic with .env creds"
  echo "  ./run.sh cisco all        Run check + NETCONF + interface"
  echo
  echo "Examples:"
  echo "  ./run.sh cisco gnmic get --path openconfig-interfaces:interfaces"
  echo "  ./run.sh cisco gnmic --encoding ascii get --path 'show version'"
  echo
  echo "Short forms also work: ?, help, check, netconf, interface, gnmic, all"
}

run_check() {
  "${PYTHON_BIN}" simple_xr_automation.py
}

run_netconf() {
  "${PYTHON_BIN}" ios_xr_automation.py
}

run_interface() {
  "${PYTHON_BIN}" ios_xr_interface_automation.py
}

run_gnmic() {
  if ! command -v gnmic >/dev/null 2>&1; then
    echo "Error: gnmic is not installed or not in PATH"
    echo "Install: bash -c \"\$(curl -sL https://get-gnmic.openconfig.net)\""
    exit 1
  fi

  "${PYTHON_BIN}" - "$@" <<'PY'
import subprocess
import sys

from config import load_xr_config

cfg = load_xr_config()
user_args = sys.argv[1:]
if not user_args:
    user_args = ["get", "--path", "openconfig-interfaces:interfaces"]
elif user_args[0] in {"?", "help"}:
    user_args = ["--help"]

cmd = [
    "gnmic",
    "--address", f"{cfg['hostname']}:{cfg['gnmi_port']}",
    "--username", cfg["username"],
    "--password", cfg["password"],
    "--insecure",
]

has_encoding = any(
    arg == "--encoding" or arg.startswith("--encoding=") or arg == "-e"
    for arg in user_args
)
if not has_encoding:
    cmd.extend(["--encoding", "JSON_IETF"])

cmd.extend(user_args)

raise SystemExit(subprocess.run(cmd).returncode)
PY
}

if [[ -x "../xr_venv/bin/python" ]]; then
  PYTHON_BIN="../xr_venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if [[ $# -eq 0 ]]; then
  show_help
  exit 0
fi

if [[ "${1}" == "cisco" ]]; then
  cmd="${2:-?}"
  shift_count=2
else
  cmd="${1}"
  shift_count=1
fi

if (( $# >= shift_count )); then
  gnmic_args=("${@:$((shift_count + 1))}")
else
  gnmic_args=()
fi

case "${cmd}" in
  "?"|help)
    show_help
    ;;
  check)
    run_check
    ;;
  netconf)
    run_netconf
    ;;
  interface)
    run_interface
    ;;
  gnmic)
    run_gnmic "${gnmic_args[@]}"
    ;;
  all)
    run_check
    run_netconf
    run_interface
    ;;
  *)
    echo "Unknown command: ${cmd}"
    echo "Try: ./run.sh cisco ?"
    exit 1
    ;;
esac
