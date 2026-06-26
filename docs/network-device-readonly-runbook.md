# Network device read-only inventory

This runbook covers `collect_network_device_inventory_readonly` for one managed
network device exposed through an operator-managed local CLI wrapper.

Tecrax owns the domain meaning of the intent, workflow, validation and normalized
result. RExecOp owns lifecycle and connector execution. GovEngine owns admission.
SCLite owns evidence and receipts. The wrapper, target address, SSH key material,
legacy SSH compatibility settings and any device-specific login setup stay outside
the repository.

## Operator prerequisites

- a local command named `tecrax-network-cli-readonly` on the operator host `PATH`;
- wrapper arguments limited to `system-info` and `ssh-status`;
- no generic passthrough mode for arbitrary device CLI commands;
- no write commands, configuration mode, reload, restart, password, VLAN, firewall,
  DNS, NTP, port security or SNMP configuration changes;
- private keys, known-hosts data and legacy SSH settings outside the repository;
- environment YAML outside the repository for real targets.

## Profile shape

The bundled connector `network_device_cli` uses `local_shell_readonly` and fixed
command shapes:

```text
tecrax-network-cli-readonly system-info
tecrax-network-cli-readonly ssh-status
```

The normalizer keeps only bounded device identity and management SSH status. It
does not preserve operator contact/location fields or user-account listings in
the normalized result.

Parser support is explicit per public fixture family:

- `tplink_sg2452_v1` for the bounded TL-SG2452 system/SSH status projection;
- `hpe_v1910_comware5` for the bounded HPE V1910 Comware 5 system/SSH status projection.

Any unsupported or prompt-drifted output must normalize to `complete=false` so the
validation rule fails closed. Do not add a generic parser that tries to infer arbitrary
network-device CLI output.

## Current operator targets

The private operator environment may map real devices to sanitized target
aliases. These aliases are safe to reference in receipts and operator notes; real
addresses, SSH key paths, known-hosts files and local wrapper paths are not.

- `tplink-switch-01` - TP-Link TL-SG2452 read-only inventory through a private
  key-backed wrapper.
- `hp1910-switch-01` - HPE V1910-48G read-only inventory through key-backed SSH
  and the device's legacy full-CLI unlock flow.

Do not add real IP addresses, hostnames, usernames, passwords, key paths or
operator workstation paths to this repository. Real target mapping belongs in
the private environment YAML and local wrapper configuration outside Git.

## Wrapper contract

The local `tecrax-network-cli-readonly` command is an operator adapter, not a
Tecrax package API and not RExecOp core. It must keep this external behavior:

- accept exactly `system-info` or `ssh-status`;
- select the real device from private operator context, such as a private
  environment target and local environment variables;
- establish device access with strict host-key checking;
- use key-based SSH where the device supports it;
- perform any vendor-specific session preparation internally;
- emit only normalized read-only text fields expected by the Tecrax normalizer;
- return non-zero on unsupported targets, login failures or unexpected prompts;
- never provide a generic passthrough for arbitrary CLI commands.

The wrapper may contain local, device-specific compatibility logic for legacy
hardware. That logic stays outside the repository because it can include private
paths, target addresses, legacy SSH options and vendor quirks that should not
become reusable domain assumptions in RExecOp core.

## Device-specific notes

### TP-Link TL-SG2452

The current TP-Link path is a bounded read-only CLI adapter. It collects:

- system description;
- system name;
- hardware version;
- software version;
- SSH management status and legacy crypto observations.

It must not collect user lists, running configuration, VLAN tables, port security
configuration, SNMP configuration or interface inventory in this slice.
The public parser fixture lives under
`tests/fixtures/network_devices/tplink_sg2452_v1/` and contains only sanitized
system and SSH status output.

### HPE V1910-48G

The current HPE path uses key-backed SSH for login, then enters the legacy
full-CLI mode required by this device family before running read-only `display`
commands. This is a compatibility requirement of the device, not a general
Tecrax or RExecOp behavior.

It collects:

- `display version` normalized to system description, system name, hardware
  version and software version;
- `display ssh server status` normalized to SSH server status and legacy crypto
  observations.

The full-CLI unlock material must not be committed, emitted to stdout, written
to evidence, copied into receipts or stored in the private environment YAML. If
the wrapper needs this value, it must keep it in local operator state outside
Git and suppress command echo from all normalized output.

Do not run or add HPE actions that read full configuration, local users, startup
configuration, VLAN configuration, port security, SNMP communities or interface
details until a separate read-only intent explicitly defines bounded output,
redaction and validation.
The public parser fixture lives under
`tests/fixtures/network_devices/hpe_v1910_comware5/` and does not contain the
legacy full-CLI unlock material.

## Management posture lite

`assess_network_device_management_posture_readonly` reuses the same fixed wrapper
actions as inventory, then derives `tecrax.network_management_posture@1.0` from the
normalized inventory fact. It does not run additional device commands.

The current bounded findings are limited to:

- `legacy_ssh_v1_enabled`;
- `legacy_ssh_crypto_observed`;
- `ssh_server_disabled`;
- `ssh_protocol_v2_disabled`;
- `ssh_idle_timeout_unknown`;
- `ssh_max_clients_unknown`.

The posture fact keeps `running_configuration`, `port_security`, `vlans` and
`firmware_compliance` as explicit non-claims. VLAN and port-security checks need a
separate future design checkpoint with a dedicated facts contract and fixtures.

## Safety notes

This slice observes legacy management access. It may report weak or old SSH
settings as `hardening_observations`, but it does not remediate them. Hardening
actions must be separate future intents with explicit policy, validation and
operator approval.

## Baseline evidence expectations

A successful real run should produce:

- a completed RExecOp operation;
- a passing `collect_network_device_inventory_readonly.complete` validation;
- a receipt and SCLite bundle;
- no real IP addresses, private key paths, known-hosts paths, unlock material,
  passwords, user-account listings or configuration dumps in evidence.

Before treating a new device wrapper as accepted, scan the generated operation,
evidence, receipt and SCLite bundle for these forbidden values.
