#!/usr/bin/env python3
"""
LEVEL 20: Network Service Orchestration
==========================================
Topics covered:
  - Multi-step service provisioning workflows
  - Service definition → config generation → deployment → verification
  - Rollback on failure
  - Service templates and parameterization
  - Orchestration state machine
  - Real-world example: L3VPN service provisioning
"""
import socket
import time
from enum import Enum
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 20: Network Service Orchestration")
print("=" * 60)


class StepStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class OrchestrationStep:
    """A single step in an orchestration workflow."""

    def __init__(self, name, action, rollback_action=None):
        self.name = name
        self.action = action
        self.rollback_action = rollback_action
        self.status = StepStatus.PENDING
        self.result = None

    def execute(self, context):
        self.status = StepStatus.RUNNING
        try:
            self.result = self.action(context)
            self.status = StepStatus.SUCCESS
            return True
        except Exception as e:
            self.status = StepStatus.FAILED
            self.result = str(e)
            return False

    def rollback(self, context):
        if self.rollback_action:
            try:
                self.rollback_action(context)
                self.status = StepStatus.ROLLED_BACK
            except Exception:
                pass


class ServiceOrchestrator:
    """Multi-step service orchestrator with rollback support."""

    def __init__(self, service_name):
        self.service_name = service_name
        self.steps = []
        self.context = {}
        self.completed_steps = []

    def add_step(self, name, action, rollback=None):
        self.steps.append(OrchestrationStep(name, action, rollback))

    def execute(self):
        print(f"\nOrchestrating: {self.service_name}")
        print("=" * 50)
        for i, step in enumerate(self.steps):
            print(f"\n[{i + 1}/{len(self.steps)}] {step.name}...", end=" ")
            if step.execute(self.context):
                self.completed_steps.append(step)
                print("OK")
            else:
                print(f"FAILED: {step.result}")
                self._rollback()
                return False
        print(f"\n{self.service_name}: COMPLETED")
        return True

    def _rollback(self):
        print("\n>>> Rolling back...")
        for step in reversed(self.completed_steps):
            print(f"  Rolling back: {step.name}")
            step.rollback(self.context)
        print(">>> Rollback complete")


# ---------------------------------------------------------------------------
# Service Definition: Loopback Interface Provisioning
# ---------------------------------------------------------------------------
def provision_loopback_service(session, interface_name, ip_address, description):
    """Provision a loopback interface with IP and description."""
    orchestrator = ServiceOrchestrator(
        f"Loopback Provisioning: {interface_name}"
    )

    created = False

    # Step 1: Validate inputs
    def validate_inputs(ctx):
        import ipaddress
        ipaddress.IPv4Interface(f"{ip_address}/32")
        if not interface_name.startswith("Loopback"):
            raise ValueError("Interface name must start with 'Loopback'")
        if len(description) > 128:
            raise ValueError("Description too long (>128 chars)")
        ctx["interface_name"] = interface_name
        ctx["ip_address"] = ip_address
        ctx["description"] = description
        return True

    orchestrator.add_step("Validate inputs", validate_inputs)

    # Step 2: Create interface
    ifmgr_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"

    def create_interface(ctx):
        nonlocal created
        config = f"""
        <config>
          <interface-configurations xmlns="{ifmgr_ns}">
            <interface-configuration>
              <active>act</active>
              <interface-name>{ctx['interface_name']}</interface-name>
              <description>{ctx['description']}</description>
              <interface-virtual/>
            </interface-configuration>
          </interface-configurations>
        </config>
        """
        session.edit_config(target="candidate", config=config)
        session.commit()
        created = True
        return True

    def rollback_create(ctx):
        nonlocal created
        if created:
            config = f"""
            <config>
              <interface-configurations xmlns="{ifmgr_ns}">
                <interface-configuration nc:operation="delete"
                  xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                  <active>act</active>
                  <interface-name>{ctx['interface_name']}</interface-name>
                </interface-configuration>
              </interface-configurations>
            </config>
            """
            try:
                session.edit_config(target="candidate", config=config)
                session.commit()
            except Exception:
                session.discard_changes()

    orchestrator.add_step("Create interface", create_interface, rollback_create)

    # Step 3: Configure IP address
    ipv4_ns = "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-io-cfg"

    def configure_ip(ctx):
        config = f"""
        <config>
          <interface-configurations xmlns="{ifmgr_ns}">
            <interface-configuration>
              <active>act</active>
              <interface-name>{ctx['interface_name']}</interface-name>
              <ipv4-network xmlns="{ipv4_ns}">
                <addresses>
                  <primary>
                    <address>{ctx['ip_address']}</address>
                    <netmask>255.255.255.255</netmask>
                  </primary>
                </addresses>
              </ipv4-network>
            </interface-configuration>
          </interface-configurations>
        </config>
        """
        session.edit_config(target="candidate", config=config)
        session.commit()
        return True

    orchestrator.add_step("Configure IP address", configure_ip)

    # Step 4: Verify
    def verify(ctx):
        verify_filter = f"""
        <filter>
          <interface-configurations xmlns="{ifmgr_ns}">
            <interface-configuration>
              <active>act</active>
              <interface-name>{ctx['interface_name']}</interface-name>
            </interface-configuration>
          </interface-configurations>
        </filter>
        """
        resp = session.get_config(source="running", filter=verify_filter)
        xml = etree.fromstring(str(resp))
        name_elem = xml.find(f".//{{{ifmgr_ns}}}interface-name")
        if name_elem is None or name_elem.text != ctx["interface_name"]:
            raise Exception("Verification failed: interface not found")

        # Check IP
        ip_elem = xml.find(f".//{{{ipv4_ns}}}address")
        if ip_elem is None or ip_elem.text != ctx["ip_address"]:
            raise Exception("Verification failed: IP mismatch")

        return True

    orchestrator.add_step("Verify configuration", verify)

    return orchestrator


# ---------------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------------
print("\n[1] Service Orchestration Architecture")
print("-" * 40)
print("""
  Service Catalog --> Orchestrator --> NETCONF/gNMI --> Device
  -----------------------------------------------------------
  L3VPN Provision
    |-- Validate inputs
    |-- Create VRF instance
    |-- Assign interfaces to VRF
    |-- Configure BGP/MPLS
    |-- Configure route targets
    |-- Verify routing table

  Interface Provision
    |-- Validate inputs
    |-- Create interface
    |-- Configure IP address
    |-- Verify configuration
""")

# Demo service execution
print("\n[2] Executing Demo Service: Loopback299")
print("-" * 40)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:
    orchestrator = provision_loopback_service(
        session,
        interface_name="Loopback299",
        ip_address="99.99.99.99",
        description="Orchestration Demo - Level 20",
    )

    success = orchestrator.execute()
    if success:
        print(f"\n{'='*50}")
        print(f"Service deployed: Loopback299")
        print(f"  IP: 99.99.99.99/32")
        print(f"  Description: Orchestration Demo - Level 20")

        # Cleanup
        print("\n[Cleanup] Removing Loopback299...")
        cleanup_config = """
        <config>
          <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
            <interface-configuration nc:operation="delete"
              xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
              <active>act</active>
              <interface-name>Loopback299</interface-name>
            </interface-configuration>
          </interface-configurations>
        </config>
        """
        try:
            session.edit_config(target="candidate", config=cleanup_config)
            session.commit()
            print("Loopback299 removed")
        except Exception as e:
            session.discard_changes()
            print(f"Cleanup note: {e}")

print("\nKey takeaways:")
print("  - Orchestration breaks complex services into ordered, reversible steps")
print("  - Each step has an action and optional rollback action")
print("  - State machine tracks step status for audit trail")
print("  - Rollback unwinds completed steps in reverse order")
print("  - This pattern works for L3VPN, EVPN, QoS, ACL deployment")
print("  - Production orchestrators: Ansible, NSO, Itential, custom Python")
