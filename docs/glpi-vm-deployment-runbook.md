# GLPI VM deployment runbook

This runbook covers the operator-owned GLPI deployment gate for the Proxmox
stack.

GLPI is introduced as the helpdesk, inventory and incident-register layer. This
runbook keeps deployment, bootstrap credential rotation, backup, monitoring and
future integrations separate.

## Scope

The deployment pass covers:

- creating a dedicated Debian VM for GLPI;
- placing the VM on the data-service storage class;
- installing GLPI from the official upstream archive;
- using a local MariaDB database;
- exposing GLPI through a local web server with the document root set to the
  GLPI `public` directory;
- applying the normal Linux host onboarding package;
- adding local PBS and external backup coverage where approved;
- producing a public-safe sign-off.

It does not configure final GLPI workflows, mail ingestion, LDAP/SSO, GLPI
agent rollout, final alert routing, HTTPS/PKI hardening, compliance readiness or
secret storage.

## Public and Private Boundary

Safe in public docs and sign-offs:

- service role and target alias;
- deployment form and broad sizing class;
- OS family;
- GLPI source class and major line;
- database engine class;
- backup and monitoring status summaries;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- GLPI admin password, database password and app secrets;
- SSH keys, known-hosts, fingerprints and local secret paths;
- raw database dumps and uploaded files;
- mail credentials, LDAP bind credentials and API tokens;
- full private topology or user inventory.

## Placement

Recommended public-safe shape:

- deployment class: Proxmox VM;
- OS family: Debian;
- storage class: data-service HDD mirror pool;
- initial disk: moderate helpdesk/inventory class;
- CPU and memory: small application/database VM, expandable after real usage;
- service alias: `glpi01`;
- operator account follows the environment hard rule: `rexecop`.

Prefer a VM over a CT for this service because GLPI combines the web
application, database-backed state, plugins, uploads, inventory data and future
mail/LDAP integrations.

## Installation Source

Use upstream GLPI release artifacts and official installation documentation.
Do not use unreviewed third-party installer scripts.

The web server document root must point to GLPI's `public` directory for modern
GLPI releases.

## Procedure

### 1. Preflight

Validate before VM creation:

- the selected service address is unused;
- data-service storage has enough free capacity;
- local DNS and NTP are healthy;
- PBS is reachable;
- the GLPI release source is an official upstream artifact;
- bootstrap credentials will be rotated by the operator after first login.

### 2. Create VM

Create a dedicated VM with static network configuration, QEMU guest agent,
serial console and operator access. Keep credentials outside Git.

The VM should use the local infrastructure DNS/time model:

- resolver follows the AD/AdGuard authority decision;
- NTP client uses the local Proxmox time source.

### 3. Install GLPI

Install the web server, PHP runtime and required PHP extensions, MariaDB,
archive tools and supporting packages from operating-system repositories.
Include the PHP `bcmath` extension; modern GLPI releases treat it as mandatory.

Install GLPI from the official archive into the application path. Configure the
web server so the document root is the GLPI `public` directory.

Create a local database and database user using generated credentials stored
only on the host/application configuration path.

Run GLPI CLI commands as the web application user, not as a normal operator
shell user, because the application configuration and logs should not be world
readable.

### 4. Bootstrap And Rotation

Complete the initial GLPI setup through the operator-owned path. Any temporary
or default credentials must be rotated immediately by the operator.

Do not paste new credentials into Git, chat, sign-offs or runbooks.

### 5. Monitoring And Backup

Apply the Linux host onboarding package:

- local time synchronization;
- `zabbix-agent2` active checks and Zabbix host registration when credential is
  available;
- Wazuh infrastructure agent enrollment where applicable;
- backup eligibility decision.

Add local PBS backup coverage. Include the VM in the external base-services
backup job if it is part of the base operational stack.

Run first manual local PBS and external backup proofs before signing off
deployment.

### 6. Restore Proof

Before claiming GLPI as a durable helpdesk/inventory system, restore it to an
isolated temporary target or equivalent controlled path and validate web login,
database state and uploaded files.

This restore proof may be a separate gate.

## Validation

Validate:

- VM is running;
- SSH through the operator account works;
- guest agent reports;
- local time synchronization is healthy;
- GLPI web endpoint returns the setup or login page;
- database service is active;
- web service and PHP runtime are active;
- Zabbix agent baseline is healthy after onboarding;
- Wazuh agent is active after onboarding;
- local PBS backup job exists and first manual backup completed;
- no secret appears in public Tecrax docs or sign-offs.

## Stop Conditions

Stop before sign-off if any of these are true:

- generated database credential or admin credential would be exposed;
- service address conflicts with an existing workload;
- upstream source cannot be obtained from an official release path;
- GLPI web setup/login does not work;
- bootstrap credentials cannot be rotated by the operator;
- backup coverage cannot be created or first backup fails;
- deployment requires mail, LDAP or API secrets before vault/custody is ready.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `glpi-vm-deployment`;
- service alias and deployment class;
- OS family and broad sizing class;
- GLPI source class and major line;
- monitoring validation summary;
- backup coverage summary;
- bootstrap credential rotation status;
- explicit non-claims.

Non-claims:

- no final helpdesk workflow yet;
- no LDAP/SSO claim;
- no mail ingestion claim;
- no final HTTPS/TLS hardening or private CA trust claim;
- no GLPI agent rollout claim;
- no compliance readiness claim;
- no one-command disaster recovery claim.
