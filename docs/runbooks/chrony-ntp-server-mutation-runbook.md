# Chrony NTP server mutation

This runbook describes `configure_chrony_ntp_server`, a registered mutation candidate
in Tecrax for one host to serve NTP through chrony for one declared IPv4 LAN subnet.
Default RExecOp `stable_read_only` blocks apply before connector I/O, so Tecrax is not
mutation_ready.

The candidate contract is deterministic. An LLM may propose or explain the change, but
it has no execution authority. If a separately qualified posture ever exists, its path
would be:

```text
Tecrax intent -> RExecOp plan -> GovEngine admission -> Tecrax connector backend
-> RExecOp lifecycle -> SCLite evidence
```

## Scope

The registered candidate contract is limited to:

- one managed file: `/etc/chrony/conf.d/tecrax-ntp-server.conf`;
- one strict IPv4 CIDR with prefix `/24` or narrower;
- chrony config parse validation by the operator wrapper in live mode;
- chrony service restart by the operator wrapper in live mode;
- post-state confirmation that the desired server state is applied.

The operation does not configure clients, firewall policy, upstream server
identity, DNS, DHCP, VM settings, storage, Proxmox cluster state or any generic
shell command.

## Operator prerequisites

- the access handoff in `../proxmox-access-handoff.md` is complete;
- target access uses the `rexecop` account;
- real target binding, SSH keys and known-hosts files stay outside Git;
- live execution uses an operator-owned wrapper outside Git;
- GovEngine admission is required before any future `apply` consideration;
- no unattended apply is allowed; default RExecOp `stable_read_only` still blocks before
  connector I/O.

The public example uses `fixture_only: true`. A live environment must replace it
with an operator-owned wrapper command. The wrapper is not a Tecrax public API;
it is local operator infrastructure that must implement only the fixed actions
declared by the `chrony_ntp_server` connector.

## Deterministic action contract

Connector: `chrony_ntp_server`

Backend: `tecrax_chrony_ntp`

Actions:

- `read_chrony_ntp_server_state`;
- `apply_chrony_ntp_server`;
- `rollback_chrony_ntp_server`.

The backend validates `allowed_subnet` as a strict IPv4 CIDR and rejects networks
broader than `/24`. In live mode it invokes the wrapper with fixed argv, never a
rendered shell command.

## Wrapper output boundary

RExecOp owns subprocess execution and incrementally enforces one combined
stdout-plus-stderr capture limit. The Chrony backend consumes that runtime
primitive and only owns fixed argv, wrapper JSON validation and Tecrax domain
defaults. The configured default is exactly `16384` bytes; an exact positive
integer request policy may lower, but not raise, the configured limit.

Crossing the combined limit is always an unsuccessful
`output_limit_exceeded` result, even if the wrapper exits zero or emits valid
JSON. The response is raw-free: it includes only the effective limit,
per-stream SHA-256 digests, per-stream truncation flags and exact observed
stdout, stderr and total byte counts. It contains no retained stdout/stderr,
argv, raw JSON, return code or peak-retention field. A timeout likewise exposes
no raw or partial output. Successful stderr is not projected.

This boundary does not qualify the private wrapper or a live Chrony target, and
it does not claim a digest for bytes a terminated child did not emit. It does
not grant retry or rollback authority; those remain a separate T-204
qualification. It does not change `lab_only`, mutation readiness, permits,
consume-once behavior or rollback conformance.

## Run

Use the sanitized fixture environment only to inspect candidate planning shape without
touching infrastructure. It does not make Tecrax mutation_ready:

```bash
rexecop plan --profile tecrax \
  --env examples/environments/chrony-ntp-server.apply.example.yaml \
  --intent configure_chrony_ntp_server \
  --target chrony-host-01 \
  --mode apply
```

In production, keep the real environment file outside Git and use a private
target alias. Do not commit real host addresses, wrapper paths, SSH paths,
known-hosts paths or operation identifiers.

## Validation

The profile validation checks candidate shape only:

- mutation state exists for `apply_chrony_ntp_server`;
- post-state reports `desired_state_applied=true`;
- SCLite receipt generation is part of the workflow.

The evidence intentionally carries bounded state only. It does not preserve raw
SSH output, private hostnames, fingerprints, key paths, local wrapper paths,
upstream identities or client lists.
