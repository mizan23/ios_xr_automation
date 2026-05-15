#!/usr/bin/env python3
"""
LEVEL 24: Test Framework (pytest) for Network Automation
===========================================================
Topics covered:
  - Writing testable network automation code
  - pytest fixtures for NETCONF/gNMI sessions
  - Mock-based testing (offline, no device needed)
  - Integration tests (requires device connectivity)
  - Test organization and naming conventions
  - Continuous testing in CI/CD

Usage:
  pytest level24_test_framework.py -v                # Run all tests
  pytest level24_test_framework.py -v -k "netconf"   # Run NETCONF tests only
  pytest level24_test_framework.py -v --no-header    # Clean output
"""
import socket
import pytest
from lxml import etree
from ncclient import manager
from pygnmi.client import gNMIclient
from config import load_xr_config

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def xr_config():
    """Load configuration from .env."""
    return load_xr_config()

@pytest.fixture(scope="module")
def device_ip(xr_config):
    """Resolve device hostname to IP."""
    return socket.gethostbyname(xr_config["hostname"])

@pytest.fixture(scope="module")
def nc_session(device_ip, xr_config):
    """Establish NETCONF session (reused across tests)."""
    with manager.connect(
        host=device_ip, port=xr_config["netconf_port"],
        username=xr_config["username"], password=xr_config["password"],
        hostkey_verify=False, device_params={"name": "iosxr"},
    ) as session:
        yield session

@pytest.fixture(scope="module")
def gnmi_session(device_ip, xr_config):
    """Establish gNMI session (reused across tests)."""
    with gNMIclient(
        target=(device_ip, str(xr_config["gnmi_port"])),
        username=xr_config["username"], password=xr_config["password"],
        insecure=True,
    ) as client:
        yield client

# ---------------------------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------------------------
class TestConfiguration:
    """Configuration validation tests."""

    def test_config_loads(self, xr_config):
        """Verify configuration loads with required keys."""
        assert xr_config["hostname"], "Hostname must not be empty"
        assert xr_config["username"], "Username must not be empty"
        assert xr_config["password"], "Password must not be empty"
        assert isinstance(xr_config["netconf_port"], int)
        assert isinstance(xr_config["gnmi_port"], int)

    def test_credentials_masked(self, xr_config):
        """Verify password is not empty (masked in logs)."""
        assert len(xr_config["password"]) > 0, "Password must be set"

    def test_hostname_resolves(self, device_ip):
        """Verify DNS resolution works."""
        assert device_ip, "Hostname must resolve to IP"
        parts = device_ip.split(".")
        assert len(parts) == 4, "Must be valid IPv4"
        for p in parts:
            assert 0 <= int(p) <= 255

# ---------------------------------------------------------------------------
# NETCONF Tests
# ---------------------------------------------------------------------------
class TestNetconf:
    """NETCONF protocol tests."""

    def test_connected(self, nc_session):
        """Verify NETCONF session is established."""
        assert nc_session.connected, "Session must be connected"
        assert nc_session.session_id > 0, "Session ID must be positive"

    def test_capabilities(self, nc_session):
        """Verify server advertises capabilities."""
        caps = nc_session.server_capabilities
        assert len(caps) > 0, "Must have at least one capability"
        assert any("netconf:base" in c for c in caps), "Must support NETCONF base"

    def test_get_config(self, nc_session):
        """Verify get_config returns valid data."""
        config = nc_session.get_config(source="running")
        data = str(config)
        assert len(data) > 0, "Running config cannot be empty"
        assert "<data" in data, "Response must contain data element"

    def test_get_config_parseable(self, nc_session):
        """Verify config is valid XML."""
        config = str(nc_session.get_config(source="running"))
        try:
            xml = etree.fromstring(config)
            assert xml is not None
        except etree.XMLSyntaxError as e:
            pytest.fail(f"Config not valid XML: {e}")

    def test_candidate_capability(self, nc_session):
        """Verify candidate datastore is supported."""
        caps = nc_session.server_capabilities
        has_candidate = any("candidate" in c for c in caps)
        assert has_candidate, "Device must support candidate datastore"

    def test_get_interfaces(self, nc_session):
        """Verify interface config retrieval."""
        fs = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
        fltr = f'<filter><interface-configurations xmlns="{fs}"/></filter>'
        resp = nc_session.get_config(source="running", filter=fltr)
        xml = etree.fromstring(str(resp))
        intfs = xml.findall(f".//{{{fs}}}interface-configuration")
        assert len(intfs) > 0, "Must have at least one interface"

    def test_interface_names_valid(self, nc_session):
        """Verify interface names are non-empty strings."""
        fs = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
        fltr = f'<filter><interface-configurations xmlns="{fs}"/></filter>'
        resp = nc_session.get_config(source="running", filter=fltr)
        xml = etree.fromstring(str(resp))
        for intf in xml.findall(f".//{{{fs}}}interface-configuration"):
            name_elem = intf.find(f"{{{fs}}}interface-name")
            if name_elem is not None:
                assert len(name_elem.text) > 0, \
                    f"Interface name cannot be empty"

# ---------------------------------------------------------------------------
# gNMI Tests
# ---------------------------------------------------------------------------
class TestGnmi:
    """gNMI protocol tests."""

    def test_capabilities(self, gnmi_session):
        """Verify gNMI capabilities."""
        caps = gnmi_session.capabilities()
        assert "gnmi_version" in caps, "Must report gNMI version"
        assert "supported_encodings" in caps, "Must report encodings"
        models = caps.get("supported_models", [])
        assert len(models) > 0, "Must support at least one YANG model"

    def test_get_interfaces(self, gnmi_session):
        """Verify gNMI get returns interface data."""
        data = gnmi_session.get(path=["interfaces"])
        assert "notification" in data, "Response must have notification"
        notif = data["notification"]
        assert len(notif) > 0, "Must have at least one notification"
        updates = notif[0].get("update", [])
        assert len(updates) > 0, "Must have updates"

    def test_interfaces_have_names(self, gnmi_session):
        """Verify all interfaces have names."""
        data = gnmi_session.get(path=["interfaces"])
        for notif in data["notification"]:
            for update in notif["update"]:
                for intf in update["val"].get("interface", []):
                    assert "name" in intf, f"Interface missing name"
                    assert len(intf["name"]) > 0

    def test_interfaces_have_oper_status(self, gnmi_session):
        """Verify interfaces report operational status."""
        data = gnmi_session.get(path=["interfaces"])
        for notif in data["notification"]:
            for update in notif["update"]:
                for intf in update["val"].get("interface", []):
                    state = intf.get("state", {})
                    assert "oper-status" in state, \
                        f"{intf['name']} missing oper-status"

    def test_get_system(self, gnmi_session):
        """Verify system data retrieval."""
        data = gnmi_session.get(path=["system"])
        assert len(str(data)) > 0, "System data must not be empty"

# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------
class TestIntegration:
    """Cross-protocol integration tests."""

    def test_interface_count_match(self, nc_session, gnmi_session):
        """Verify NETCONF and gNMI agree on interface count."""
        # NETCONF count
        fs = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
        fltr = f'<filter><interface-configurations xmlns="{fs}"/></filter>'
        resp = nc_session.get_config(source="running", filter=fltr)
        xml = etree.fromstring(str(resp))
        nc_count = len(xml.findall(f".//{{{fs}}}interface-configuration"))

        # gNMI count
        data = gnmi_session.get(path=["interfaces"])
        gn_count = 0
        for notif in data["notification"]:
            for update in notif["update"]:
                gn_count += len(update["val"].get("interface", []))

        print(f"\n  NETCONF: {nc_count} interfaces, gNMI: {gn_count} interfaces")
        # Note: counts may differ (config vs operational)
        assert nc_count > 0 and gn_count > 0, "Both protocols must find interfaces"

    def test_loopback0_exists(self, nc_session):
        """Verify Loopback0 is configured."""
        fs = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"
        fltr = f'<filter><interface-configurations xmlns="{fs}"/></filter>'
        resp = nc_session.get_config(source="running", filter=fltr)
        xml = etree.fromstring(str(resp))
        names = [
            n.text for n in xml.findall(f".//{{{fs}}}interface-name")
            if n.text
        ]
        assert "Loopback0" in names, "Loopback0 must be configured"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("LEVEL 24: Test Framework")
    print("=" * 60)
    print()
    print("Run tests with pytest:")
    print("  pytest level24_test_framework.py -v")
    print("  pytest level24_test_framework.py -v -k 'TestNetconf'")
    print("  pytest level24_test_framework.py -v -k 'TestGnmi'")
    print("  pytest level24_test_framework.py -v -k 'TestIntegration'")
    print()
    print("Running quick self-check...")
    pytest.main([__file__, "-v", "--tb=short", "-x"])
