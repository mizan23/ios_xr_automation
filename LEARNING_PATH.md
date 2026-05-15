# IOS XR Automation — Complete Learning Path (24 Levels)

> **Beginner → Expert → Master**: Hands-on NETCONF + gNMI automation on Cisco IOS XR

---

## Quick Reference

| Level | Script | Protocol | Topic | Status |
|-------|--------|----------|-------|--------|
| **BEGINNER (1-6)** |
| 1 | `level01_netconf_connect.py` | NETCONF | Connection, 845 capabilities, IETF standards | ✓ |
| 2 | `level02_netconf_get_config.py` | NETCONF | get_config(), XML parsing, operational data | ✓ |
| 3 | `level03_netconf_filter_xml.py` | NETCONF | Subtree filters, containment, specific leafs | ✓ |
| 4 | `level04_netconf_xpath_filter.py` | NETCONF | XPath predicates, starts-with, position | ✓ |
| 5 | `level05_netconf_edit_config.py` | NETCONF | MERGE/REPLACE/DELETE, candidate commit | ✓ |
| 6 | `level06_gnmi_get.py` | gNMI | Capabilities, Get operations, protobuf→dict | ✓ |
| **INTERMEDIATE (7-8)** |
| 7 | `level07_gnmi_subscribe.py` | gNMI | ONCE/SAMPLE/ON_CHANGE subscriptions | ✓ |
| 8 | `level08_netconf_interface_lifecycle.py` | NETCONF | Full CRUD: create, verify, update, delete | ✓ |
| **ADVANCED (9-12)** |
| 9 | `level09_reconciliation.py` | Both | Config vs state reconciliation | ✓ |
| 10 | `level10_error_handling.py` | Both | Retry logic, exponential backoff, exceptions | ✓ |
| 11 | `level11_telemetry_pipeline.py` | gNMI | Collect→Transform→Analyze→Export | ✓ |
| 12 | `level12_multi_device.py` | Both | ThreadPoolExecutor, inventory, templates | ✓ |
| **EXPERT (13-14)** |
| 13 | `level13_bgp_monitoring.py` | Both | BGP neighbor analysis, health scoring | ✓ |
| 14 | `level14_master_suite.py` | Both | Full CLI tool (health/interfaces/bgp/full) | ✓ |
| **ADVANCED EXPERT (15-19)** | | | |
| 15 | `level15_netconf_notifications.py` | NETCONF | Event streaming, create_subscription | ✓ |
| 16 | `level16_restconf.py` | RESTCONF | HTTP/JSON alternative, requests library | ✓ |
| 17 | `level17_yang_schema.py` | NETCONF | get-schema, model analysis, validation | ✓ |
| 18 | `level18_config_backup.py` | NETCONF | Backup, diff, restore, git versioning | ✓ |
| 19 | `level19_gnmi_set.py` | gNMI | Set operations (update/replace/delete) | ✓ |
| **MASTER (20-24)** | | | |
| 20 | `level20_service_orchestration.py` | Both | Multi-step workflows, rollback, state machine | ✓ |
| 21 | `level21_benchmarking.py` | Both | Latency, throughput, protocol comparison | ✓ |
| 22 | `level22_compliance.py` | Both | Policy-as-code, security audit, scoring | ✓ |
| 23 | `level23_logging_monitoring.py` | Both | Structured JSON logs, Prometheus metrics, audit | ✓ |
| 24 | `level24_test_framework.py` | Both | pytest fixtures, unit/integration tests | ✓ |

**Original toolkit scripts:**
| Script | Purpose |
|--------|---------|
| `config.py` | Loads `.env`, validates credentials, provides defaults |
| `simple_xr_automation.py` | Credential sanity check |
| `ios_xr_automation.py` | Full NETCONF demo (config + capabilities) |
| `ios_xr_interface_automation.py` | NETCONF query for single interface |
| `ios_xr_gnmi_automation.py` | gNMI get on interfaces + network-instances |

---

## Your Device at a Glance

```
Device:     sandbox-iosxr-1.cisco.com (131.226.217.150)
NETCONF:    Port 830 — 845 capabilities (153 OpenConfig, 740 Cisco, 61 IETF)
gNMI:       Port 57777 — 1,116 supported YANG models
RESTCONF:   Port 443/8080 (sandbox dependent)

Interfaces: 12 (GigabitEthernet0/0/0/0, Gi0/0/0/1, Loopback0/2/10/99/123/199, 
            Bundle-Ether11212/12345, MgmtEth0/RP0/CPU0/0, Null0)

BGP:        AS 1, Router-ID 1.1.1.1, Neighbor 2.2.2.2 (IDLE), 6 prefixes

Features:   Candidate datastore, confirmed commit, rollback, validate, 
            notifications, interleave — all supported
```

---

## Learning Path (Recommended Order)

### Phase 1: Foundation (30 min)
Run these to understand the basics:
```bash
python simple_xr_automation.py          # Verify .env credentials
python level01_netconf_connect.py       # Explore 845 capabilities
python level06_gnmi_get.py              # First gNMI experience
```

### Phase 2: NETCONF Core (1 hr)
```bash
python level02_netconf_get_config.py    # Pull and parse running config
python level03_netconf_filter_xml.py    # Subtree filters
python level04_netconf_xpath_filter.py  # XPath power
python level05_netconf_edit_config.py   # Make configuration changes
```

### Phase 3: gNMI Core (45 min)
```bash
python level06_gnmi_get.py              # gNMI Get operations
python level07_gnmi_subscribe.py        # Streaming telemetry
python level19_gnmi_set.py              # gNMI configuration
```

### Phase 4: Production Patterns (1.5 hr)
```bash
python level09_reconciliation.py        # Config vs state
python level10_error_handling.py        # Robust operations
python level11_telemetry_pipeline.py    # Data pipeline
python level12_multi_device.py          # Parallel ops
python level13_bgp_monitoring.py        # BGP analysis
```

### Phase 5: Advanced Protocols (1 hr)
```bash
python level15_netconf_notifications.py # Event streaming
python level16_restconf.py              # HTTP alternative
python level17_yang_schema.py           # Schema exploration
```

### Phase 6: Operations & DevOps (1 hr)
```bash
python level18_config_backup.py         # Backup & restore
python level20_service_orchestration.py # Workflow engine
python level21_benchmarking.py          # Performance testing
python level22_compliance.py            # Security audit
```

### Phase 7: Production Readiness (1 hr)
```bash
python level23_logging_monitoring.py    # Structured logging + metrics
python level24_test_framework.py        # pytest tests
python level14_master_suite.py health   # Master CLI tool
```

---

## Key Concepts Learned

### NETCONF
- SSH transport on port 830, XML encoding
- `<get-config>` for config, `<get>` for state+config
- Subtree filters (XML containment) vs XPath filters (path expressions)
- Candidate datastore → validate → commit → discard workflow
- Confirmed commit for automatic rollback
- Capabilities reveal all supported YANG models and NETCONF features

### gNMI
- gRPC/HTTP2 transport on port 57777, Protobuf encoding
- `get()` for point-in-time data, `subscribe()` for streaming
- ONCE = single snapshot, SAMPLE = periodic, ON_CHANGE = push on change
- `set()` for configuration (update/replace/delete)
- JSON_IETF and ASCII encoding options
- Vendor-neutral OpenConfig paths: `interfaces`, `system`, `network-instances`

### Protocol Selection

| Need | Use |
|------|-----|
| Full config management | NETCONF (candidate datastore, transactions) |
| Real-time telemetry | gNMI subscribe (streaming native) |
| Quick state queries | gNMI get (JSON output, fast) |
| Configuration changes | NETCONF (rollback, validate) |
| DevOps/CI integration | RESTCONF (HTTP, JSON) |
| Multi-vendor portability | gNMI + OpenConfig paths |

---

## Key Discoveries From This Sandbox

1. **Interface names are in `<interface-name>`, not `<active>` text**
   - `<active>act</active>` means "active"; `<interface-name>Loopback0</interface-name>` is the name
   - `<active>pre</active>` means "preconfigured"

2. **gNMI requires IP address (not hostname) and port as string**
   ```python
   target = (ip, str(port))  # Correct
   ```

3. **gNMI get paths work without namespace prefix**
   ```python
   client.get(path=["interfaces"])  # Works
   # client.get(path=["openconfig-interfaces:interfaces"])  # May fail
   ```

4. **NETCONF edit-config uses `nc:operation="delete"` for removals**

5. **Sandbox connection limits apply — avoid rapid reconnects**

---

## Running All Tests

```bash
pip install pytest
pytest level24_test_framework.py -v
```

Tests validate:
- Configuration loading
- NETCONF connectivity, capabilities, get-config
- gNMI connectivity, Get operations, interface data
- Cross-protocol integration (interface count consistency)
- Interface naming standards

---

## Files Generated During Execution

| File | Source Level | Purpose |
|------|-------------|---------|
| `config_backups/*.xml` | 18 | Configuration backup snapshots |
| `config_backups/*.json` | 18 | Backup metadata |
| `telemetry_*.json` | 11 | Telemetry data export |
| `report_*.json` | 14, 22 | Compliance/audit reports |
| `xr_automation.log` | 23 | Structured JSON logs |
| `audit.log` | 23 | Immutable audit trail |

---

## Next Steps Beyond This Project

1. **Multi-vendor**: Adapt scripts for Arista EOS, Juniper Junos, Nokia SR OS
2. **CI/CD Pipeline**: GitHub Actions workflow running compliance checks
3. **Ansible Integration**: Wrap scripts as Ansible modules
4. **Database Backend**: Store telemetry in InfluxDB/TimescaleDB
5. **Dashboard**: Grafana dashboard from Prometheus metrics
6. **Intent-Based**: Declare desired state, let orchestrator converge
7. **Kubernetes**: Run as CronJob in K8s for scheduled compliance

---

## Troubleshooting

**SSH connection reset**: Sandbox has connection limits. Wait 30 seconds between scripts.

**gNMI timeout**: Use IP address (not hostname), port as string. Check `--insecure` flag.

**Module not found**: Run `python -m pip install -r requirements.txt`.

**No `.env` file**: Create `.env` with `XR_USERNAME` and `XR_PASSWORD`.
