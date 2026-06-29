# Zabbix VM Docker deployment runbook

This runbook covers the operator-owned deployment gate for Zabbix as the first
monitoring service in the Proxmox environment.

It is not an active Tecrax mutation and does not add a Zabbix-administration
connector. Tecrax already has bounded read-only Zabbix summary intents; this
runbook documents how the monitored Zabbix service is introduced before those
read-only checks are adopted against the live stack.

## Scope

The deployment pass covers:

- creating a dedicated Debian VM for Zabbix;
- placing the VM on the data-service storage class;
- installing Docker Engine and Docker Compose from the official Docker apt
  repository;
- deploying Zabbix with official Zabbix containers;
- using PostgreSQL as the database backend;
- validating service health, DNS, time sync and reboot behavior;
- adding PBS VM-level backup coverage;
- producing a public-safe sign-off.

It does not tune final monitoring templates, migrate all infrastructure devices,
configure production alert routing, expose Zabbix API credentials to Tecrax,
activate Wazuh/Grafana integration, or claim disaster-recovery coverage.

## Public and Private Boundary

Safe in public docs and sign-offs:

- generic target aliases and service roles;
- deployment form: VM;
- broad sizing class;
- OS family;
- Zabbix major line and backend type;
- bounded service status;
- backup status summary;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- real addresses, host fingerprints, key paths and local target catalogs;
- database passwords, API tokens, web admin passwords and recovery material;
- raw Compose environment files if they contain secrets;
- raw logs, screenshots or command output that reveal private topology;
- complete monitored-host inventory until classified as safe;
- backup repository URLs and backup contents.

## Placement

Recommended public-safe shape:

- deployment class: Proxmox VM;
- OS family: Debian;
- storage class: data-service HDD mirror pool;
- disk size: 120 GB at initial deployment;
- CPU and memory: small monitoring VM, expandable after retention is known;
- hostname alias: `zbx01`;
- operator account follows the environment hard rule: `rexecop`.

Prefer a VM over a CT for this service. Docker inside LXC adds nesting,
AppArmor, storage-driver and restore complexity. A VM gives Zabbix a normal
kernel boundary and makes PBS restore behavior simpler.

## Version Choice

Use the current supported Zabbix LTS line unless there is an explicit reason to
use the current feature release. At the time this runbook was written, the
operator choice for this environment is:

```text
Zabbix line: 7.0 LTS
Backend: PostgreSQL
Frontend: web nginx container
Deployment: Docker Compose
```

Do not use unpinned `latest` images for the live stack. Pin the Zabbix image
line and PostgreSQL image line in the Compose file or `.env` controlled by the
operator.

## Installation Source

Use primary upstream sources:

- Docker Engine from the official Docker apt repository for Debian;
- Zabbix containers and Compose definitions from the official
  `zabbix/zabbix-docker` repository or an operator-owned minimal Compose file
  using official Zabbix images.

Do not pipe convenience install scripts into a root shell. Avoid third-party
Compose files unless they are explicitly reviewed and vendored by the operator.

## Deployment Procedure

### 1. Preflight

Validate before VM creation:

- the selected service address is unused;
- Proxmox storage has enough free capacity;
- PBS is reachable;
- DNS authority model is healthy;
- local NTP service is healthy;
- the Debian cloud image or install media has a known source;
- operator has break-glass console access.

### 2. Create the VM

Create a dedicated VM with cloud-init or an equivalent deterministic install
path. Enable QEMU guest agent and serial console. Set the static network
configuration through operator-owned Proxmox metadata.

The VM should use the local DNS/time model:

- DNS resolver follows the AD/AdGuard authority decision for infrastructure
  servers;
- NTP client uses the local Proxmox time source.

### 3. Prepare the OS

On first boot:

- validate SSH as `rexecop`;
- validate passwordless sudo if automation will continue through that account;
- install and enable QEMU guest agent;
- update base packages;
- configure chrony or equivalent NTP client to use the local time source;
- set a predictable hostname;
- keep any local key paths and known-hosts material outside Git.

### 4. Install Docker

Install Docker Engine through the official Docker apt repository:

- remove conflicting distro packages if present;
- install the Docker apt keyring and repository;
- install `docker-ce`, `docker-ce-cli`, `containerd.io`,
  `docker-buildx-plugin` and `docker-compose-plugin`;
- enable and start Docker;
- validate with `docker version` and `docker compose version`.

Do not add broad users to the Docker group unless the operator accepts the
root-equivalent implications.

### 5. Deploy Zabbix

Deploy a minimal single-node Zabbix stack:

- PostgreSQL database container;
- Zabbix server container with PostgreSQL backend;
- Zabbix web frontend container with nginx;
- optional Zabbix agent only if needed for local self-monitoring.

Use operator-owned secret material for database credentials. Keep `.env`,
Docker secrets and generated passwords outside public Tecrax artifacts.

Set conservative initial retention in the Zabbix UI or configuration before
adding broad discovery. The initial goal is to observe the base stack, not to
ingest every possible metric.

### 6. Validate

Validate after deployment:

- VM boots and guest agent reports;
- SSH as `rexecop` works;
- local NTP source is selected;
- Docker service is active;
- all expected Compose services are running or healthy;
- Zabbix web UI is reachable through the operator-approved path;
- Zabbix server listens on the expected trapper port;
- PostgreSQL container is persistent across restart;
- DNS can resolve base infrastructure names;
- Zabbix can monitor at least its own server or a first low-risk host;
- no secret appears in public Tecrax docs or sign-offs.

### 7. Reboot Proof

Reboot the VM once before sign-off. After reboot, validate again:

- network returns;
- SSH as `rexecop` works;
- guest agent is reachable;
- local NTP source is selected;
- Docker starts automatically;
- Compose stack returns;
- Zabbix web UI and server are reachable.

### 8. Backup

Add a PBS VM-level backup job for the Zabbix VM after the stack is healthy.

Because Zabbix state is database-backed, VM-level backup is not the only desired
future claim. Add a later gate for PostgreSQL logical dumps or another
application-aware database backup path before treating Zabbix history as
recoverable at application level.

## Stop Conditions

Stop before sign-off if any of these are true:

- service address conflict or unresolved stale gateway binding;
- DNS authority model is unhealthy;
- local NTP source is unavailable;
- Docker installation requires a third-party script;
- Compose stack requires exposing database or web credentials to LLM/tooling;
- PostgreSQL state is not persistent;
- PBS is unavailable and no alternate backup path is approved;
- reboot proof fails;
- evidence would require publishing secrets, raw topology or host fingerprints.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `zabbix-vm-docker-deployment`;
- target alias: `zbx01`;
- deployment form;
- broad VM sizing;
- OS family;
- Zabbix major line and backend;
- Docker/Compose health summary;
- Zabbix service health summary;
- NTP/DNS validation summary;
- reboot proof summary;
- backup status;
- explicit non-claims.

Non-claims:

- no full monitoring coverage yet;
- no final alerting policy;
- no Grafana dashboard integration;
- no Wazuh integration;
- no Zabbix API credential custody in Tecrax;
- no application-aware database restore proof yet;
- no external disaster-recovery copy.

## Next Gate

After the Zabbix VM is deployed and signed off, add the first monitored targets
in this order:

1. Zabbix VM self-monitoring.
2. Proxmox host availability and storage posture.
3. PBS service health and backup-job state.
4. Samba AD DC DNS/Kerberos/service health.
5. AdGuard DNS/web/service health.
6. Admin-tools availability.

Only after initial targets are stable should Grafana dashboards or Wazuh log
monitoring become active work packages.
