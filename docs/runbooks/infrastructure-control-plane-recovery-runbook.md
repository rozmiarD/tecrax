# Infrastructure control-plane recovery runbook

This runbook covers the operator-owned protection of the infrastructure control
plane when workload backups alone are insufficient for disaster recovery. It
keeps Proxmox VE configuration, Proxmox Backup Server configuration and managed
network-device configuration as separate encrypted artifacts under one bounded
recovery procedure.

This is a public-safe `L1` runbook. It does not activate a Tecrax backup intent,
ship a generic SSH executor, authorize a live device import or claim full
disaster-recovery readiness.

## Ownership boundary

- Tecrax owns the infrastructure meaning, gates, non-claims and this runbook.
- RExecOp owns domain-neutral execution lifecycle if this procedure is later
  promoted to an active governed operation.
- GovEngine owns admission, approval requirements and policy decisions.
- SCLite owns canonical evidence and receipts through existing contracts.
- Private operator context owns real targets, paths, recipient fingerprints,
  device commands and environment-bound helpers.
- Runtime secret custody owns private keys, device unlock material and other
  credentials.

Do not add lifecycle, retry orchestration, admission or a competing evidence
format to a Tecrax script or private helper.

## Scope

The procedure may cover:

- an independently protected bootstrap PKI virtual machine before production CA
  material exists;
- the bounded host and guest-definition configuration needed to rebuild a
  Proxmox VE substrate;
- the official Proxmox Backup Server configuration boundary plus package and
  storage-layout manifests;
- encrypted off-device configuration exports for explicitly approved managed
  network devices;
- checksum comparison and memory-only decrypt/content validation.

It does not cover:

- backing up a complete PBS datastore as a generic VM archive merely to close a
  coverage checkbox;
- production CA key custody or application-level CA export;
- direct NAS administration, internal NAS inspection or deletion;
- live import of a network-device configuration;
- replacement-host PVE/PBS rebuild proof;
- automatic pruning or an implicit retention policy. Recurring capture is
  allowed only as an explicitly approved, bounded schedule with health
  monitoring and append-only storage semantics.

## Public and private boundary

Safe in this repository:

- artifact classes and encryption format;
- generic host roles and supported device families;
- preflight, stop conditions and validation requirements;
- explicit non-claims and evidence shape.

Must remain outside Git:

- real target mappings and addresses;
- mount points and internal storage paths;
- certificate fingerprints and private-key paths;
- raw PVE, PBS or device configurations;
- device commands when they reveal private platform state;
- unlock secrets, credentials and private keys;
- exact recovery artifact locations and retention inventory.

## Artifact and encryption model

Raw configuration must flow directly from the source process into encryption
and must never be written as a plaintext file. The current operator procedure
uses CMS EnvelopedData with a dedicated RSA recipient and AES-256-CBC content
encryption. Only the public recipient certificate is available on the runtime
host. The recovery private key remains in separate operator custody.

The encrypted artifacts use `.p7m`. A bounded manifest may contain timestamps,
artifact names, sizes, hashes and non-claims, but no configuration values,
credentials or secret material.

Checksums detect accidental transfer corruption in the proven path. They do not
by themselves prove artifact origin against a malicious writer. A later
signature or authenticated-manifest decision is a separate hardening gate.

## Required operator helper behavior

The environment-bound helper stays outside this repository and must:

- default to a non-mutating plan;
- require an explicit `--apply` for artifact creation;
- read targets, paths and certificate identity from private operator context;
- fail closed on runtime and remote host identity;
- use an exact source/device allowlist;
- reject unexpected prompts, small captures and CLI error markers;
- keep raw archives and device configurations only in process memory;
- write files with private permissions;
- refuse to overwrite an existing run identifier or artifact;
- copy only encrypted artifacts and bounded manifests off-host;
- emit only non-secret result metadata;
- provide a workstation-side validation mode that writes no plaintext.

The helper is not an RExecOp replacement. It must not implement queueing,
automatic retries, governance admission, generic arbitrary-command passthrough
or reusable lifecycle semantics.

## Procedure

### 1. Establish authority and identity

Record the exact authorized source roles, runtime host, off-host storage class
and network devices. Confirm live aliases resolve to the expected host identity
and that the approved runtime helper and recipient certificate are present.

Stop if a target, role, VM identifier, certificate or storage class is
ambiguous.

### 2. Preserve bootstrap PKI substrate

When the PKI VM contains no production CA material, it may be added to the
approved independent VM backup job after an exact pre-state and rollback are
recorded. Run a first manual backup and require a successful result plus one new
artifact.

Rollback may remove the workload from the schedule. It must not delete the
created off-host artifact. Before production CA material exists, replace this
bootstrap rule with a dedicated CA custody and export procedure.

### 3. Plan the control-plane bundle

Run the private helper in plan mode. Confirm:

- no mutation is reported;
- the expected PVE and PBS roles are selected;
- the intended network-device allowlist is exact;
- plaintext disk writes are disabled;
- the private key is absent from runtime custody;
- the off-host storage is reachable through its supported mounted interface.

Do not log in to the NAS management plane merely to validate the mounted backup
target.

### 4. Create the encrypted PVE/PBS bundle

After explicit authorization, run the helper with `--apply` and a unique run
identifier. Collect only the bounded configuration and rebuild manifests needed
for the approved PVE/PBS recovery model.

Require:

- exact source-host assertions;
- encrypted runtime artifacts;
- a non-secret manifest;
- encrypted off-host copies;
- equality of runtime and off-host checksums;
- no raw archive on disk.

An encrypted configuration bundle makes PBS rebuildable; it does not make a
co-located datastore an independent backup.

### 5. Create encrypted network-device exports

Use only the device-specific read-only export commands approved in private
operator context. Handle legacy prompts and pagers explicitly. Never provide a
generic CLI passthrough.

Reject the export if output is too small, contains a command-error marker or
does not return to the exact expected prompt. Encrypt before durable storage,
then copy only encrypted artifacts and the bounded manifest off-device.

Reading a saved or running configuration is sensitive even when password fields
appear hashed. Never print or attach the raw output to evidence.

### 6. Schedule a recurring device-configuration capture

Schedule only an exact, separately approved device export. Do not reuse a
recurring job as authority to discover or add other devices.

The scheduled mechanism must:

- remain fail closed on the runtime host and exact device identity;
- capture both running and startup configuration and reject a mismatch;
- use a non-overlapping lock and a unique run identifier;
- encrypt before any durable write;
- copy only encrypted artifacts and a bounded manifest off-host;
- verify off-host checksums during every run;
- publish only a minimal health aggregate for monitoring;
- alert on failure, incomplete artifact shape and stale last success;
- keep encrypted artifacts append-only without automatic delete or prune.

The monitoring aggregate may expose success, age and artifact/checksum counts.
It must not expose raw configuration, addresses, credentials, hashes of secret
values or storage paths. A monitoring problem may enter the normal
infrastructure ticket-routing path, but a healthy run must not create a ticket.

The recovery private key must not be copied to the scheduler. Perform the
initial decrypt/read smoke from separate recovery-key custody, then repeat it at
an explicitly documented interval. Checksum validation on the scheduler does
not replace decrypt/read validation.

### 7. Validate recovery readability

From the private-key custody workstation, stream each encrypted artifact from
runtime custody into the decrypt process. Keep plaintext only in process memory.

For PVE/PBS, require the approved archive members and package/storage manifests.
For network devices, require bounded size and line counts and absence of CLI
error markers. Record only counts and pass/fail status.

This proves encryption roundtrip and bounded content readability. It is not a
replacement-host rebuild or live device-import proof.

### 8. Record persistence and delivery status

Before sign-off, record:

- public-safe runbook/profile status;
- private helper promotion and runtime synchronization status;
- tests and live validation status;
- repository delivery status;
- custody, cadence, retention and restore-test follow-ups.

Do not delete a temporary helper until it has been promoted, replaced by an
existing stack mechanism or explicitly classified as non-repeatable.

## Stop conditions

Stop if any of these are true:

- authorization does not cover every selected source or device;
- host identity, recipient certificate or storage target differs from private
  operator context;
- a raw archive or configuration would be written to disk;
- the private recovery key is required on the runtime host;
- the destination run identifier already exists;
- a network prompt or pager is unsupported;
- a source capture is incomplete or contains an error marker;
- running and startup configurations differ;
- a previous scheduled execution still holds the operation lock;
- off-host checksum equality cannot be proven;
- success would require NAS deletion or management-plane access;
- the requested claim requires a replacement rebuild or live import that was
  not separately authorized.

## Rollback and failure boundary

Configuration-job rollback must be prepared before changing backup coverage.
Encrypted recovery artifacts are append-only under this runbook. Do not delete
or prune them without a separate retention decision and, for NAS-hosted data,
the immediate operation-specific authorization required by the NAS safety
model.

If an upload fails, keep the runtime encrypted artifact and record the off-host
copy as incomplete. Do not hide or automatically delete a partial off-host
artifact.

## Sign-off shape

Record only:

- date and run class;
- selected generic source/device roles;
- encryption and private-key-custody class;
- artifact and checksum counts;
- decrypt/content validation results;
- plaintext-written-to-disk status;
- DSM/NAS mutation status;
- helper/runbook/runtime-sync/repository-delivery status;
- open custody, cadence, retention, rebuild and import gates.

Explicit non-claims:

- no production CA custody proof;
- no independent copy of a co-located PBS datastore;
- no replacement PVE/PBS rebuild proof;
- no live network-device import proof;
- no NAS-internal recovery proof;
- no NIS2/KSC2 compliance-readiness claim.

## Next gates

- physical offline break-glass custody of the recovery private key;
- approved recurring cadence and off-host retention;
- isolated replacement PVE/PBS rebuild validation;
- vendor-specific import validation in an approved maintenance window;
- optional signed or authenticated manifest design during hardening.

Current activation level: `L1 - public-safe runbook` plus a private,
environment-bound operator helper family for one-shot and scheduled capture
outside the package.
