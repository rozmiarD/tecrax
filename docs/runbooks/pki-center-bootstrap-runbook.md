# PKI Center bootstrap runbook

This runbook covers the first PKI Center bootstrap for the Tecrax/MBP
infrastructure stack.

PKI Center is a security-sensitive, on-demand VM for internal certificate
operations. This bootstrap creates the substrate and operating boundaries. It
does not generate production CA material, distribute a trust root, or claim final
HTTPS rollout.

## Scope

The bootstrap covers:

- creating a dedicated Proxmox VM for PKI Center;
- placing the VM on the critical-light storage class;
- installing a minimal Debian OS;
- keeping the VM on-demand and powered off by default after bootstrap checks;
- adding VM-level backup coverage before CA material exists;
- documenting the custody boundary for future CA work;
- producing a public-safe sign-off.

It does not create a root CA, intermediate CA, private keys, trust stores,
keystores, certificate inventory, endpoint trust deployment, renewal automation,
revocation workflow, or final HTTPS enforcement.

## Public and Private Boundary

Safe in public docs and sign-offs:

- service alias, VM class and storage class;
- OS family and broad sizing;
- powered-off/on-demand status;
- backup coverage status;
- decision status for CA tooling and model;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- CA private keys, passphrases and keystores;
- root/intermediate material and exports;
- recovery material and break-glass procedure details;
- certificate signing requests containing private topology beyond approved
  public-safe aliases;
- private certificate inventory, renewal calendars and distribution details;
- raw OpenSSL/easyrsa/cfssl/smallstep config containing organization-private
  values.

## Placement

Recommended public-safe shape:

- deployment class: Proxmox VM;
- service alias: `pki01`;
- OS family: Debian stable minimal;
- storage class: `rpool` / critical-light SSD mirror;
- initial disk: small critical-service class;
- CPU and memory: small on-demand service, expandable after tool choice;
- operator account follows the environment hard rule: `rexecop`.

Use a VM rather than a CT. PKI material is high-sensitivity infrastructure
state, and the VM boundary gives a cleaner model for isolation, backup, restore
proof and later hardening.

## Bootstrap Security Model

PKI Center starts with status `bootstrap-substrate`, not `trusted CA`.

During substrate bootstrap:

- do not generate production CA keys;
- do not store CA passphrases in Git, chat, roadmap or public sign-offs;
- do not leave the VM exposed as a normal always-on web service;
- power the VM off by default after installation and validation;
- record only public-safe operational facts.

Required gates before trusted CA usage:

- CA tool decision;
- root/intermediate model decision;
- private custody and offline break-glass model;
- encrypted CA material storage model;
- VM-level and application/export backup model;
- isolated PKI restore proof;
- Proxmox root-of-trust hardening checkpoint;
- trust-root distribution plan.

## Procedure

### 1. Preflight

Validate before VM creation:

- selected VM ID and service address are unused;
- `rpool` has enough capacity;
- operator account and SSH key model are ready;
- DNS/NTP baseline is available;
- no CA material needs to be created during this bootstrap;
- backup target is available for a substrate backup;
- monitoring does not page on expected powered-off state.

### 2. Create VM

Create a dedicated VM with:

- static network configuration;
- QEMU guest agent;
- serial console;
- operator account;
- DNS following the infrastructure AD/DNS authority model;
- time synchronized to the local hierarchy.

Keep bootstrap credentials outside Git and public docs.

### 3. Install Minimal Substrate

Install only minimal packages needed for secure administration and future CA
tool evaluation:

- OS updates;
- QEMU guest agent;
- OpenSSL and certificate inspection tools;
- basic archive/checksum tools;
- no production CA stack until the tool decision is made.

### 4. Backup And Power State

Create VM-level backup coverage before any CA material exists.

After validation:

- keep the VM powered off by default;
- start it only for CA work, maintenance, backup/restore proof or controlled
  hardening;
- do not enroll it in normal always-on service alerting unless the monitoring
  policy explicitly supports expected-off hosts.

## Validation

Validate:

- VM exists on the intended storage class;
- operator SSH works while VM is on;
- passwordless sudo works for `rexecop`;
- QEMU guest agent responds;
- OS time and DNS are correct;
- no production CA material exists;
- VM-level backup job exists and first substrate backup completed;
- VM is powered off after bootstrap sign-off unless the operator explicitly
  keeps it on.

## Stop Conditions

Stop before sign-off if:

- production CA keys would be generated without a custody model;
- CA passphrases or exports would be printed or committed;
- backup or restore target is unavailable;
- the VM would become an always-on exposed service without a hardening decision;
- monitoring would create noisy false incidents for expected powered-off state;
- deployment would require treating the VM as trusted CA before restore and
  custody gates.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `pki-center-bootstrap`;
- service alias and deployment class;
- OS family and broad sizing;
- power-state model;
- backup summary;
- CA material status;
- explicit non-claims.

Non-claims:

- no production CA;
- no CA private keys;
- no trust-root distribution;
- no service HTTPS migration;
- no PKI restore proof;
- no final trusted CA status;
- no secret values in the sign-off.

## Tecrax Artifact Target

Current target: `L1` public-safe runbook.

Future candidates:

- `L3` read-only certificate inventory and expiry checks;
- `L3` PKI backup/restore-proof status checks;
- no early L4 CA mutation before custody and policy gates.
