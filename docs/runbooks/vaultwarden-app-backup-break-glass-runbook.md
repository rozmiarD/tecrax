# Vaultwarden application backup and break-glass baseline runbook

This runbook covers the first application-level backup and offline break-glass
baseline for the Vaultwarden bootstrap service.

Vaultwarden remains in `bootstrap` status. This runbook does not authorize full
password migration, final trusted custody, formal NIS2/KSC2 compliance claims or
AI access to secrets.

## Scope

The baseline covers:

- root-owned application backup of the Vaultwarden data directory;
- consistent SQLite database copy using SQLite backup mechanics;
- private manifest and checksum evidence;
- explicit distinction between application backup and user vault export;
- offline break-glass architecture requirements;
- public-safe sign-off shape.

It does not cover:

- reading, dumping or exporting vault secret values;
- storing backup archives in Tecrax, chat or public sign-offs;
- automated off-host replication of vault data;
- retention pruning;
- MFA rollout;
- final PKI/TLS integration;
- Proxmox root-of-trust hardening.

## Public And Private Boundary

Safe in public docs and sign-offs:

- run class and service alias;
- backup method;
- backup location class, without exposing sensitive paths if not needed;
- manifest/checksum existence;
- `sqlite quick_check` result;
- service health after backup;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- Vaultwarden database contents;
- backup archives containing vault data;
- user vault exports;
- admin token, passwords, MFA recovery codes and emergency sheets;
- backup encryption keys;
- private restore targets and raw logs.

## Backup Model

The first application-level backup is a local root-owned artifact. It is not a
replacement for VM-level PBS backups or off-host disaster recovery.

Recommended properties:

- archive is readable only by root;
- manifest is readable only by root;
- SQLite database copy is created with `.backup`, not by dumping rows;
- WAL/SHM and temporary files are excluded from the final archive;
- archive checksum is recorded in a private manifest;
- no retention pruning happens until a retention policy exists;
- no user vault export is created unless the operator deliberately performs it
  outside AI/repo/chat.

## Procedure

### 1. Preflight

Validate:

- Vaultwarden service is healthy;
- persistent data directory exists;
- backup destination is root-owned and local to the host;
- operator understands that the archive contains sensitive vault data;
- no command will print database rows, config secrets or recovery material.

### 2. Create Application Backup

Run the operator-owned helper on the Vaultwarden host:

```sh
sudo /usr/local/sbin/vaultwarden-app-backup
```

The public-safe helper template is kept at
`scripts/vaultwarden-app-backup.sh`. Install it to the host-controlled path
after operator review.

The helper should:

- create a temporary root-only work directory;
- copy `db.sqlite3` through SQLite `.backup`;
- run `PRAGMA quick_check` on the copied database;
- archive the copied database and non-database Vaultwarden data files;
- write a private manifest with backup id, timestamp, checksum and quick-check
  result;
- leave `latest` symlinks for operator convenience;
- avoid printing secret values.

### 3. Validate Backup Artifact

Validate only metadata and archive integrity:

```sh
sudo test -r /var/backups/vaultwarden/app/latest.tar.gz
sudo test -r /var/backups/vaultwarden/app/latest.manifest.txt
sudo tar -tzf /var/backups/vaultwarden/app/latest.tar.gz >/dev/null
```

Do not list restored vault contents in public logs. Do not inspect database
rows.

### 4. Offline Break-Glass Baseline

The break-glass path must not depend only on Vaultwarden.

At minimum, the operator should maintain an offline package that can recover
access to:

- Proxmox/PBS administrative path;
- Vaultwarden administrative path;
- backup repository access path;
- PKI/root recovery path when PKI material exists;
- emergency contact and authorization notes.

Preferred physical model:

- encrypted USB drive used only for break-glass material;
- USB drive stored offline in a physical safe;
- recovery access limited to explicitly authorized roles, initially Director
  and IT administrator;
- recovery action requires a recorded reason, date and people involved;
- recovery material is never copied to Tecrax, BookStack, chat, ordinary
  workstation folders or AI tooling;
- any printed companion sheet must contain only handling instructions and role
  names unless the operator deliberately approves a separate sealed-secret
  packet.

Tecrax may document the existence, owner roles, test cadence and non-secret
evidence. It must not document the USB passphrase, recovery codes, exported
vault files, private keys or backup repository credentials.

The offline USB package should be tested through a metadata-only drill first:
confirm that authorized people can locate the safe, identify the package and
follow the recovery checklist without exposing any secret values. Full recovery
tests must use an isolated target and a separately approved scope.

### 5. Future Promotion Gate

Vaultwarden can move from `bootstrap` to `production trusted custody` only after
separate gates are complete:

- VM-level restore proof;
- application backup proof;
- offline break-glass material prepared and tested by the operator;
- MFA/recovery policy;
- PKI/HTTPS integration;
- Proxmox root-of-trust hardening checkpoint;
- backup/off-host custody decision.

## Validation

The baseline passes only if:

- application backup completes;
- SQLite quick check returns `ok`;
- archive checksum matches manifest;
- archive and manifest are root-only;
- Vaultwarden remains healthy after backup;
- no secret values are printed, committed or copied into public docs;
- sign-off records remaining gates before final trusted custody.

## Stop Conditions

Stop if:

- backup would require printing or exporting secret values;
- archive permissions cannot be restricted;
- SQLite quick check fails;
- service health changes after backup;
- operator expects local application backup to replace VM-level PBS or off-host
  recovery;
- break-glass material would be stored in Vaultwarden only.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `vaultwarden-app-backup-break-glass-baseline`;
- service alias;
- backup method;
- manifest/checksum evidence without secret values;
- service health after backup;
- offline break-glass status;
- explicit non-claims.

Non-claims:

- no vault content inspection;
- no user vault export;
- no full password migration approval;
- no final trusted custody;
- no formal compliance claim;
- no secret custody in Tecrax.

## Tecrax Artifact Target

Current target: `L1` public-safe runbook plus private operator sign-off.

Future candidates:

- `L3` read-only check for newest manifest age and checksum presence;
- `L3` restore-proof status summary;
- no L4 operation that reads, exports or rotates vault secret values.
