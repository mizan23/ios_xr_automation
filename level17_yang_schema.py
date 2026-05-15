#!/usr/bin/env python3
"""
LEVEL 17: YANG Schema Exploration & Data Validation
======================================================
Topics covered:
  - YANG model structure (module, container, list, leaf)
  - Retrieving YANG schemas from device (get-schema)
  - Parsing YANG models programmatically
  - Validating configuration against YANG model
  - Mapping between OpenConfig and Cisco native models
  - Building model-aware automation tools
"""
import socket
from lxml import etree
from ncclient import manager
from config import load_xr_config

cfg = load_xr_config()
ip = socket.gethostbyname(cfg["hostname"])

print("=" * 60)
print("LEVEL 17: YANG Schema Exploration & Validation")
print("=" * 60)

with manager.connect(
    host=ip, port=cfg["netconf_port"],
    username=cfg["username"], password=cfg["password"],
    hostkey_verify=False, device_params={"name": "iosxr"},
) as session:

    # 1. Retrieve YANG schema for a model
    print("\n[1] Retrieving YANG Schema (get-schema)")
    print("-" * 40)

    models_to_fetch = [
        ("Cisco-IOS-XR-ifmgr-cfg", "2019-04-05"),
        ("Cisco-IOS-XR-ipv4-bgp-cfg", "2023-09-06"),
        ("openconfig-interfaces", "2024-01-31"),
    ]

    for model_name, revision in models_to_fetch:
        schema_rpc = f"""
        <get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
          <identifier>{model_name}</identifier>
          <version>{revision}</version>
          <format>yang</format>
        </get-schema>
        """
        try:
            result = session.dispatch(etree.fromstring(schema_rpc))
            data_xml = result.xml
            if "<data>" in data_xml:
                # Extract schema content
                schema_start = data_xml.find("<data>") + 6
                schema_end = data_xml.find("</data>")
                schema_text = data_xml[schema_start:schema_end]
                lines = schema_text.count("\n")
                size = len(schema_text)
                print(f"  {model_name}: {size} bytes, ~{lines} lines")

                # Show key YANG constructs
                containers = schema_text.count("container ")
                lists = schema_text.count("list ")
                leafs = schema_text.count("leaf ")
                print(f"    containers: {containers}, lists: {lists}, leafs: {leafs}")
            else:
                print(f"  {model_name}: schema not returned")
        except Exception as e:
            print(f"  {model_name}: {str(e)[:80]}")

    # 2. Schema-driven capability analysis
    print("\n[2] Schema-Aware Capability Analysis")
    print("-" * 40)
    caps = session.server_capabilities

    # Extract YANG modules from capability URIs
    openconfig_modules = set()
    cisco_modules = set()
    ietf_modules = set()

    for cap in caps:
        if "module=" in cap:
            import re
            match = re.search(r"module=([^&]+)", cap)
            if match:
                module = match.group(1)
                if "openconfig" in cap.lower():
                    openconfig_modules.add(module)
                elif "cisco" in cap.lower():
                    cisco_modules.add(module)
                elif "ietf" in cap.lower():
                    ietf_modules.add(module)

    print(f"  Unique OpenConfig modules: {len(openconfig_modules)}")
    print(f"  Unique Cisco modules: {len(cisco_modules)}")
    print(f"  Unique IETF modules: {len(ietf_modules)}")

    print("\n  Top OpenConfig modules:")
    for m in sorted(openconfig_modules)[:8]:
        print(f"    - {m}")

    # 3. Model mapping: OpenConfig ↔ Cisco native
    print("\n[3] Model Mapping: OpenConfig → Cisco Native")
    print("-" * 40)
    mapping = {
        # OpenConfig model -> Cisco native equivalents
        "openconfig-interfaces": ["Cisco-IOS-XR-ifmgr-cfg", "Cisco-IOS-XR-um-interface-cfg"],
        "openconfig-bgp": ["Cisco-IOS-XR-ipv4-bgp-cfg", "Cisco-IOS-XR-um-router-bgp-cfg"],
        "openconfig-network-instance": ["Cisco-IOS-XR-um-vrf-cfg"],
        "openconfig-routing-policy": ["Cisco-IOS-XR-um-route-policy-cfg"],
        "openconfig-mpls": ["Cisco-IOS-XR-mpls-ldp-cfg", "Cisco-IOS-XR-um-mpls-ldp-cfg"],
        "openconfig-lldp": ["Cisco-IOS-XR-ethernet-lldp-cfg", "Cisco-IOS-XR-um-lldp-cfg"],
        "openconfig-acl": ["Cisco-IOS-XR-ipv4-acl-cfg", "Cisco-IOS-XR-um-ipv4-access-list-cfg"],
    }
    for oc, cisco in mapping.items():
        available = [c for c in cisco if c in cisco_modules]
        print(f"  {oc:<35} → {', '.join(available) if available else '(none found)'}")

    # 4. Configuration validation pattern
    print("\n[4] Configuration Validation Pattern")
    print("-" * 40)
    print("IOS XR supports validate RPC to check candidate config:")
    print("  session.validate(source='candidate')")
    print()
    print("Validation workflow:")
    print("  1. edit_config(target='candidate', ...)")
    print("  2. validate('candidate')  # Check YANG compliance")
    print("  3. If OK → commit()")
    print("  4. If error → discard_changes(), fix, retry")
    print()
    print("Validation catches:")
    print("  - Missing required leafs")
    print("  - Invalid data types (string where uint expected)")
    print("  - Pattern/regex mismatches")
    print("  - Range violations (MTU out of bounds)")
    print("  - Must constraint violations")
    print("  - Unique constraint violations")
    print("  - When constraint failures")

    # 5. Build a model explorer
    print("\n[5] YANG Model Explorer Tool")
    print("-" * 40)
    print("Usage pattern for model exploration:")
    print("""
    def explore_model(session, model_name):
        '''Fetch and analyze a YANG model from the device.'''
        schema = get_schema(session, model_name)
        return {
            'name': model_name,
            'containers': extract_containers(schema),
            'lists': extract_lists(schema),
            'leafs': extract_leafs(schema),
            'augments': extract_augments(schema),
            'typedefs': extract_typedefs(schema),
        }
    """)

    print("\nKey takeaways:")
    print("  - get-schema RPC retrieves full YANG model text from device")
    print("  - YANG models define the contract for NETCONF/RESTCONF/gNMI operations")
    print("  - Model validation prevents incorrect configurations")
    print("  - OpenConfig provides vendor-neutral models; Cisco native adds extensions")
    print("  - Schema-aware tools can auto-generate configuration templates")
    print("  - pyang or yangson libraries can parse YANG locally for offline validation")
