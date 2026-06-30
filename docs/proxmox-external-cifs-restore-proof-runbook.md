# Proxmox external CIFS restore proof runbook

This runbook covers the first restore proof from an external CIFS backup target
for the Proxmox deployment.

It is intentionally narrow: restore one low-risk workload to a temporary ID,
validate the restored configuration and filesystem, and remove the temporary
workload without starting it on the production network.

## Scope

This gate covers:

- selecting a low-risk backup artifact from the external CIFS storage;
- restoring it to an unused temporary VMID or CTID;
- keeping the restored workload stopped unless an isolated network is prepared;
- validating restored configuration and filesystem readability;
- destroying the temporary restore target after validation;
- recording public-safe sign-off evidence.

It does not prove full disaster recovery, application-level consistency for all
services, PBS datastore off-host recovery, automated infrastructure rebuild or
restore of secrets.

## Public and Private Boundary

Safe in public docs and sign-offs:

- storage class and non-secret storage alias;
- restored workload role or alias;
- temporary restore class, such as unused CTID or VMID;
- validation summary;
- cleanup confirmation;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- CIFS endpoint address, share path and credentials;
- backup contents;
- raw logs containing private topology;
- hardware addresses, host fingerprints and secret paths;
- production network details beyond already-approved aliases.

## Prerequisites

- External CIFS backup gate is complete.
- Proxmox reports the external CIFS storage as active.
- At least one backup artifact exists for the selected low-risk workload.
- A temporary VMID or CTID is confirmed unused.
- The operator has decided whether the restored workload may be started. The
  default for this first proof is: do not start it.

## Procedure

### 1. Select the restore target

Choose a low-risk workload with a recent backup artifact. For the first proof,
prefer a small CT over a critical VM.

Confirm the temporary VMID or CTID does not already exist.

### 2. Restore to the temporary ID

Restore from the external CIFS storage to the temporary ID.

Use restore options that avoid identity collision where available, such as
regenerating unique hardware identity. Do not rely on that alone for network
safety, because static addressing can still be restored from the original
configuration.

### 3. Keep the workload stopped

Do not start the restored workload on the production bridge if it still contains
production addressing or service identity.

If a boot test is required later, prepare an isolated bridge or disabled network
configuration first.

### 4. Validate

Validate:

- the restored VM/CT exists under the temporary ID;
- the restored workload is stopped;
- restored configuration is readable;
- root storage was recreated on the intended storage;
- filesystem can be mounted or inspected offline;
- expected operating-system markers and base directories exist.

### 5. Cleanup

Unmount any offline mount and destroy the temporary restore workload.

Validate:

- the temporary VM/CT no longer exists;
- temporary restore storage was removed;
- the production workload remained untouched.

## Stop Conditions

Stop before sign-off if any of these are true:

- the backup artifact cannot be listed from Proxmox;
- temporary VMID or CTID is already in use;
- restore would overwrite a production workload;
- validation requires starting a restored workload with production addressing;
- temporary storage cannot be cleaned up;
- the result is being described as full disaster recovery.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `proxmox-external-cifs-restore-proof`;
- storage class and storage alias;
- restored workload role;
- temporary restore class;
- validation summary;
- cleanup summary;
- explicit non-claims.

Non-claims:

- no full disaster recovery proof;
- no automated rebuild proof;
- no application-level restore proof for every service;
- no PBS datastore off-host recovery proof;
- no secret restore proof.

## Next Gate

Repeat restore proof for higher-risk workloads only when an isolated restore
network and service-specific validation checklist exist. Keep full automated DR
restore as a late-stage milestone after the infrastructure shape stabilizes.
