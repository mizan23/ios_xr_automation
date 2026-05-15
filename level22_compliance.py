#!/usr/bin/env python3
"""
LEVEL 22: Configuration Compliance & Audit
==============================================
Topics covered:
  - Golden configuration templates
  - Compliance checking (audit against standards)
  - Policy-based configuration validation
  - Security hardening checks
  - Generating compliance reports
  - Continuous compliance monitoring
"""
import socket
import re
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 22: Configuration Compliance & Audit")
print("=" * 60)

# ---------------------------------------------------------------------------
# Compliance Rules
# ---------------------------------------------------------------------------
COMPLIANCE_RULES = [
    {
        "id": "SEC-001",
        "severity": "HIGH",
        "category": "Security",
        "description": "SSH server must be enabled",
        "check_type": "xpath",
        "path": "//{http://cisco.com/ns/yang/Cisco-IOS-XR-crypto-ssh-cfg}ssh",
        "expect_present": True,
    },
    {
        "id": "SEC-002",
        "severity": "MEDIUM",
        "category": "Security",
        "description": "Telnet server should be disabled",
        "check_type": "regex",
        "pattern": r"<telnet.*/>",
        "expect_match": False,
    },
    {
        "id": "IFACE-001",
        "severity": "HIGH",
        "category": "Interface",
        "description": "Loopback0 must exist",
        "check_type": "xpath",
        "path": "//{http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg}interface-name[text()='Loopback0']",
        "expect_present": True,
    },
    {
        "id": "IFACE-002",
        "severity": "MEDIUM",
        "category": "Interface",
        "description": "All interfaces should have descriptions",
        "check_type": "custom",
    },
    {
        "id": "IFACE-003",
        "severity": "LOW",
        "category": "Interface",
        "description": "No shutdown interfaces should be operationally UP",
        "check_type": "gnmi",
    },
    {
        "id": "BGP-001",
        "severity": "HIGH",
        "category": "Routing",
        "description": "BGP must be configured with a valid AS number",
        "check_type": "regex",
        "pattern": r"<instance-as>.*<as>(\d+)</as>",
        "expect_match": True,
    },
    {
        "id": "BGP-002",
        "severity": "HIGH",
        "category": "Routing",
        "description": "BGP router-id must be configured",
        "check_type": "regex",
        "pattern": r"<router-id>[\d.]+</router-id>",
        "expect_match": True,
    },
    {
        "id": "DNS-001",
        "severity": "MEDIUM",
        "category": "Management",
        "description": "DNS domain name should be configured",
        "check_type": "xpath",
        "path": "//{http://cisco.com/ns/yang/Cisco-IOS-XR-ip-domain-cfg}domain",
        "expect_present": True,
    },
    {
        "id": "NTP-001",
        "severity": "LOW",
        "category": "Management",
        "description": "NTP server should be configured",
        "check_type": "regex",
        "pattern": r"<ntp>",
        "expect_match": True,
    },
    {
        "id": "AAA-001",
        "severity": "MEDIUM",
        "category": "Security",
        "description": "AAA authentication must be configured",
        "check_type": "xpath",
        "path": "//{http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-locald-cfg}aaa",
        "expect_present": True,
    },
]

# ---------------------------------------------------------------------------
# Compliance Checker
# ---------------------------------------------------------------------------
class ComplianceChecker:
    def __init__(self, config_xml):
        self.xml = config_xml
        self.results = []

    def check_xpath(self, rule):
        """Check if XPath matches in config."""
        try:
            xml = etree.fromstring(self.xml)
            elements = xml.findall(rule["path"])
            found = len(elements) > 0
            passed = found == rule["expect_present"]
            return passed, f"Found {len(elements)} matching elements"
        except Exception as e:
            return False, f"XPath error: {e}"

    def check_regex(self, rule):
        """Check if regex matches in config."""
        match = re.search(rule["pattern"], self.xml)
        if rule["expect_match"]:
            passed = match is not None
            return passed, f"Match: {match.group(0)[:60] if match else 'None'}"
        else:
            passed = match is None
            return passed, "No match (as expected)" if passed else f"Unexpected match found"

    def check_custom(self, rule):
        """Custom compliance checks."""
        if rule["id"] == "IFACE-002":
            xml = etree.fromstring(self.xml)
            ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
            intfs = xml.findall(f".//{{{ns}}}interface-configuration")
            missing_desc = []
            for intf in intfs:
                name_elem = intf.find(f"{{{ns}}}interface-name")
                desc_elem = intf.find(f"{{{ns}}}description")
                if name_elem is not None and desc_elem is None:
                    missing_desc.append(name_elem.text)
            passed = len(missing_desc) == 0
            detail = (f"No descriptions: {', '.join(missing_desc[:5])}"
                      if missing_desc else "All interfaces have descriptions")
            return passed, detail
        return False, "Unknown custom check"

    def check_gnmi(self, rule):
        """Check via gNMI state."""
        if rule["id"] == "IFACE-003":
            try:
                from pygnmi.client import gNMIclient
                with gNMIclient(
                    target=(ip, str(cfg["gnmi_port"])),
                    username=cfg["username"], password=cfg["password"],
                    insecure=True,
                ) as client:
                    data = client.get(path=["interfaces"])
                    notif = data["notification"][0]
                    issues = []
                    for update in notif["update"]:
                        for intf in update["val"].get("interface", []):
                            state = intf.get("state", {})
                            if (state.get("admin-status") == "UP" and
                                    state.get("oper-status") != "UP"):
                                issues.append(intf["name"])
                    passed = len(issues) == 0
                    detail = (f"DOWN interfaces: {', '.join(issues)}"
                              if issues else "All UP interfaces operational")
                    return passed, detail
            except Exception as e:
                return False, f"gNMI error: {e}"
        return False, "Unknown gNMI check"

    def run_all(self):
        """Run all compliance checks."""
        for rule in COMPLIANCE_RULES:
            check_type = rule["check_type"]
            if check_type == "xpath":
                passed, detail = self.check_xpath(rule)
            elif check_type == "regex":
                passed, detail = self.check_regex(rule)
            elif check_type == "custom":
                passed, detail = self.check_custom(rule)
            elif check_type == "gnmi":
                passed, detail = self.check_gnmi(rule)
            else:
                passed, detail = False, f"Unknown check type: {check_type}"

            self.results.append({
                **rule,
                "passed": passed,
                "detail": detail,
            })
        return self.results

    def report(self):
        """Generate compliance report."""
        print(f"\n{'='*70}")
        print(f"  Configuration Compliance Report")
        print(f"  Device: {cfg['hostname']}")
        print(f"  Rules checked: {len(self.results)}")
        print(f"{'='*70}")

        passed = sum(1 for r in self.results if r["passed"])
        failed = len(self.results) - passed

        # Summary
        print(f"\n  PASSED: {passed}/{len(self.results)} "
              f"({passed / len(self.results) * 100:.0f}%)")
        print(f"  FAILED: {failed}/{len(self.results)}")

        # By severity
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            sev_results = [r for r in self.results if r["severity"] == sev]
            sev_pass = sum(1 for r in sev_results if r["passed"])
            status = "PASS" if sev_pass == len(sev_results) else f"{sev_pass}/{len(sev_results)}"
            print(f"  {sev}: {status}")

        # Details
        print(f"\n{'='*70}")
        print(f"  {'ID':<12} {'Severity':<10} {'Category':<14} {'Result':<8} Detail")
        print(f"  {'-'*70}")
        for r in self.results:
            result = "PASS" if r["passed"] else "FAIL"
            print(f"  {r['id']:<12} {r['severity']:<10} {r['category']:<14} "
                  f"{result:<8} {r['detail'][:40]}")
            if not r["passed"]:
                print(f"    -> {r['description']}")

        # By category
        print(f"\n{'='*70}")
        print(f"  Results by Category")
        print(f"  {'─'*70}")
        categories = {}
        for r in self.results:
            cat = r["category"]
            categories.setdefault(cat, {"total": 0, "passed": 0})
            categories[cat]["total"] += 1
            if r["passed"]:
                categories[cat]["passed"] += 1

        for cat, counts in sorted(categories.items()):
            pct = counts["passed"] / counts["total"] * 100
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"  {cat:<16} {bar} {pct:.0f}% ({counts['passed']}/{counts['total']})")

        return passed, failed


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------
with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:
    print("[*] Fetching running configuration...")
    config_xml = str(session.get_config(source="running"))
    print(f"    Config size: {len(config_xml)} chars")

    checker = ComplianceChecker(config_xml)
    checker.run_all()
    pass_count, fail_count = checker.report()

    print(f"\n{'='*70}")
    compliance_score = pass_count / len(COMPLIANCE_RULES) * 100
    print(f"  Overall Compliance Score: {compliance_score:.0f}%")
    if compliance_score >= 90:
        print("  ✓ Compliant")
    elif compliance_score >= 70:
        print("  ⚠ Needs attention")
    else:
        print("  ✗ Non-compliant — remediation required")

print("\nKey takeaways:")
print("  - Compliance rules encode organizational policy as code")
print("  - Multiple check types: XPath, regex, custom logic, gNMI state")
print("  - Severity levels prioritize remediation efforts")
print("  - Category-based reporting highlights weak areas")
print("  - Continuous compliance = scheduled checks + alerting")
print("  - Integration with CI/CD prevents non-compliant config deployment")
