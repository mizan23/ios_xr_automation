# IOS XR Automation — NETCONF & gNMI Learning Repository

> **30 Python scripts. 24 progressive levels. Beginner to Master.**  
> Hands-on network automation on Cisco IOS XR sandbox using NETCONF, gNMI, and RESTCONF.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-IOS%20XR-orange)](https://www.cisco.com/c/en/us/products/ios-nx-os-software/ios-xr-software/index.html)

---

## What This Repo Does

This repository is a complete, hands-on learning path for network automation on Cisco IOS XR. Starting from basic connectivity and progressing through telemetry pipelines, BGP monitoring, service orchestration, compliance auditing, and production-ready logging — every concept is a runnable Python script against a real device.

**No slides. No theory-only chapters. Every script connects to a live IOS XR sandbox.**

---

## Quick Start

```bash
# 1. Clone and set up
git clone <this-repo>
cd ios_xr_automation
python -m pip install -r requirements.txt

# 2. Create your .env file (gitignored)
echo XR_USERNAME=your_username > .env
echo XR_PASSWORD=your_password >> .env

# 3. Verify
python simple_xr_automation.py

# 4. Start learning
python level01_netconf_connect.py
```

---

## Project Structure

```
ios_xr_automation/
├── config.py                          # Credential loader + validation
├── simple_xr_automation.py            # Quick credential check
├── ios_xr_automation.py               # NETCONF demo (full config)
├── ios_xr_interface_automation.py     # NETCONF single-interface query
├── ios_xr_gnmi_automation.py          # gNMI get on interfaces + network-instances
├── ios_xr_automation_env.py           # Backward-compatible wrapper
│
├── level01_netconf_connect.py         # Connection, 845 capabilities, IETF standards
├── level02_netconf_get_config.py      # get_config(), XML parsing, operational data
├── level03_netconf_filter_xml.py      # Subtree filters, containment, specific leafs
├── level04_netconf_xpath_filter.py    # XPath predicates, starts-with, position
├── level05_netconf_edit_config.py     # MERGE/REPLACE/DELETE, candidate commit
├── level06_gnmi_get.py                # gNMI capabilities, Get, protobuf→dict
├── level07_gnmi_subscribe.py          # ONCE/SAMPLE/ON_CHANGE subscriptions
├── level08_netconf_interface_lifecycle.py  # Full CRUD lifecycle
├── level09_reconciliation.py          # Config vs state reconciliation
├── level10_error_handling.py          # Retry logic, exponential backoff, exceptions
├── level11_telemetry_pipeline.py      # Collect→Transform→Analyze→Export
├── level12_multi_device.py            # ThreadPoolExecutor, inventory, templates
├── level13_bgp_monitoring.py          # BGP neighbor analysis, health scoring
├── level14_master_suite.py            # Full CLI tool (health/interfaces/bgp/full)
├── level15_netconf_notifications.py   # Event streaming, create_subscription
├── level16_restconf.py                # HTTP/JSON alternative, requests library
├── level17_yang_schema.py             # get-schema, model analysis, validation
├── level18_config_backup.py           # Backup, diff, restore, git versioning
├── level19_gnmi_set.py                # Set operations (update/replace/delete)
├── level20_service_orchestration.py   # Multi-step workflows, rollback, state machine
├── level21_benchmarking.py            # Latency, throughput, protocol comparison
├── level22_compliance.py              # Policy-as-code, security audit, scoring
├── level23_logging_monitoring.py      # Structured JSON logs, Prometheus metrics, audit
├── level24_test_framework.py          # pytest fixtures, unit/integration tests
│
├── LEARNING_PATH.md                   # Detailed learning guide
├── requirements.txt                   # Python dependencies
├── run.sh                             # Bash runner (Linux/macOS/WSL)
└── .gitignore
```

---

## Learning Path

### Beginner (Levels 1–6) — Foundations

| # | Script | Protocol | Concept |
|---|--------|----------|---------|
| 1 | `level01_netconf_connect.py` | NETCONF | Connection, 845 capabilities, IETF features |
| 2 | `level02_netconf_get_config.py` | NETCONF | Pull config, lxml parsing, data stores |
| 3 | `level03_netconf_filter_xml.py` | NETCONF | Subtree filters, containment, leaf selection |
| 4 | `level04_netconf_xpath_filter.py` | NETCONF | XPath predicates, position, starts-with |
| 5 | `level05_netconf_edit_config.py` | NETCONF | MERGE/REPLACE/DELETE, candidate datastore |
| 6 | `level06_gnmi_get.py` | gNMI | Capabilities, get operations, data parsing |

### Intermediate (Levels 7–8) — Operations

| # | Script | Protocol | Concept |
|---|--------|----------|---------|
| 7 | `level07_gnmi_subscribe.py` | gNMI | ONCE, SAMPLE, ON_CHANGE streaming |
| 8 | `level08_netconf_interface_lifecycle.py` | NETCONF | Create → Verify → Update → Delete |

### Advanced (Levels 9–12) — Production Patterns

| # | Script | Protocol | Concept |
|---|--------|----------|---------|
| 9 | `level09_reconciliation.py` | Both | Config vs operational state drift |
| 10 | `level10_error_handling.py` | Both | Retry with exponential backoff |
| 11 | `level11_telemetry_pipeline.py` | gNMI | Collect → Transform → Analyze → Export |
| 12 | `level12_multi_device.py` | Both | Parallel ops, inventory, templates |

### Expert (Levels 13–19) — Protocols & Operations

| # | Script | Protocol | Concept |
|---|--------|----------|---------|
| 13 | `level13_bgp_monitoring.py` | Both | BGP neighbor state, health scoring |
| 14 | `level14_master_suite.py` | Both | CLI tool with JSON/CSV export |
| 15 | `level15_netconf_notifications.py` | NETCONF | Event streaming, subscriptions |
| 16 | `level16_restconf.py` | RESTCONF | HTTP/JSON, requests library |
| 17 | `level17_yang_schema.py` | NETCONF | Schema retrieval, model analysis |
| 18 | `level18_config_backup.py` | NETCONF | Backup, diff, restore patterns |
| 19 | `level19_gnmi_set.py` | gNMI | Configuration via gNMI Set |

### Master (Levels 20–24) — Production Readiness

| # | Script | Protocol | Concept |
|---|--------|----------|---------|
| 20 | `level20_service_orchestration.py` | Both | Multi-step workflows with rollback |
| 21 | `level21_benchmarking.py` | Both | NETCONF vs gNMI performance |
| 22 | `level22_compliance.py` | Both | Policy-as-code, security audit |
| 23 | `level23_logging_monitoring.py` | Both | JSON logs, Prometheus metrics, audit trail |
| 24 | `level24_test_framework.py` | Both | pytest with NETCONF/gNMI fixtures |

---

## Key Concepts Covered

### NETCONF
- SSH transport (port 830), XML encoding
- `<get-config>` vs `<get>`, `running`/`candidate`/`startup` datastores
- Subtree filters (XML containment) and XPath filters (predicates)
- `edit_config` with MERGE, REPLACE, DELETE operations
- Candidate datastore → `validate` → `commit` / `discard_changes`
- Confirmed commit for automatic rollback safety
- Capability discovery (IETF standard + vendor extensions)

### gNMI
- gRPC/HTTP2 transport (port 57777), Protobuf encoding
- `get()` for point-in-time state, `subscribe()` for streaming telemetry
- Subscription modes: ONCE, SAMPLE (periodic), ON_CHANGE (event-driven)
- `set()` for configuration: update, replace, delete
- JSON_IETF and ASCII encoding
- OpenConfig vendor-neutral paths

### Protocol Selection Guide

| Use Case | Protocol | Why |
|----------|----------|-----|
| Full configuration management | NETCONF | Candidate datastore, transactions, rollback |
| Real-time telemetry | gNMI | Streaming native, efficient binary transport |
| Quick state queries | gNMI | JSON output, faster than XML parsing |
| DevOps/CI integration | RESTCONF | HTTP, JSON, familiar tooling |
| Multi-vendor portability | gNMI | OpenConfig paths work across platforms |

---

## Running Tests

```bash
pip install pytest
pytest level24_test_framework.py -v         # All tests
pytest level24_test_framework.py -v -k Netconf  # NETCONF only
pytest level24_test_framework.py -v -k Gnmi     # gNMI only
```

Tests cover: configuration loading, NETCONF connectivity, gNMI get operations, interface naming validation, and cross-protocol consistency.

---

## Dependencies

```
ncclient>=0.6.0       # NETCONF client
python-dotenv>=1.0.0  # .env file loading
pygnmi>=0.8.15        # gNMI client (pip install pygnmi)
pytest>=7.0           # Test framework (optional)
requests>=2.28        # RESTCONF client (optional)
lxml>=3.3             # XML parsing (installed with ncclient)
```

Install all at once:
```bash
pip install -r requirements.txt
pip install pygnmi pytest requests
```

---

## Environment Setup

Create `.env` in the project root:

```env
XR_USERNAME=your_username
XR_PASSWORD=your_password

# Optional (defaults shown):
XR_HOSTNAME=sandbox-iosxr-1.cisco.com
XR_NETCONF_PORT=830
XR_GNMI_PORT=57777
```

`.env` is gitignored — never commit credentials.

---

## Known Sandbox Behaviors

- **Interface names** are in `<interface-name>`, not `<active>` text. `<active>act</active>` means "active"; `<active>pre</active>` means "preconfigured".
- **gNMI target** requires IP address (not hostname) and port as string: `(ip, str(port))`
- **gNMI paths** work without OC prefix: `"interfaces"` not `"openconfig-interfaces:interfaces"`
- **Sandbox connection limits** — avoid rapid reconnects. Wait 30s between scripts if you hit SSH resets.
- **RESTCONF** may not be exposed on some Cisco sandboxes — NETCONF and gNMI are the reliable options.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: dotenv` | `python -m pip install -r requirements.txt` |
| SSH connection reset | Sandbox rate limit — wait 30 seconds |
| gNMI timeout | Use IP + str(port), check `--insecure` |
| Missing `.env` keys | Create `.env` with `XR_USERNAME` and `XR_PASSWORD` |
| XPath filter returns empty | Try subtree filter instead; verify namespace prefixes |

---

## Security

- `.env` is gitignored — credentials never leave your machine
- `hostkey_verify=False` is for lab/sandbox only (never in production)
- Audit trail logging available via `level23_logging_monitoring.py`
- Compliance checking built in via `level22_compliance.py`

---

## Next Steps After This Repo

1. **Multi-vendor**: Adapt for Arista EOS, Juniper Junos, Nokia SR OS
2. **CI/CD**: GitHub Actions running compliance checks on schedule
3. **Ansible**: Wrap scripts as Ansible modules
4. **Dashboard**: Grafana over Prometheus metrics from level 23
5. **Database**: Store telemetry in InfluxDB/TimescaleDB
6. **Intent-based**: Declare desired state, let orchestrator converge

---

## License

MIT — use freely in labs, courses, and production tooling.

---

## Contributing

This is a learning repository. Found a bug? Open an issue. Want to add a level? PRs welcome — follow the numbered naming convention (`level##_descriptive_name.py`).
