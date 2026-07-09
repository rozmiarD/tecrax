# Synology NAS domain-home and GPO drive-mapping runbook

This runbook covers the controlled transition from a one-user NAS authentication
pilot to a reusable staff home-drive mapping model.

It assumes the Synology NAS is already joined to AD as a member file server and
that DSM/Samba, not GPO, remains the authority for file access. GPO is only the
client mapping layer.

## Scope

Allowed:

- validate native Synology domain home behavior for one ordinary domain user;
- confirm that the domain user's home is separate from legacy local Synology
  home directories;
- validate create/edit behavior in the user's own home;
- validate that another ordinary user cannot access that home;
- retire old pilot-only GPO links from active processing;
- prepare a neutral staff GPO/GPP drive-mapping policy for the approved home
  drive letter;
- record public-safe evidence and stop conditions.

Not allowed:

- delete, prune, purge or destructively overwrite NAS data;
- rename, merge or delete Synology local users;
- rewrite ACLs globally;
- migrate production user data;
- store NAS, AD or user credentials in GPO, scripts, Git, chat or public
  sign-offs;
- map shared spaces before their ACL model is reviewed;
- enable Offline Files or Folder Redirection without a separate decision.

## Authority Model

```text
AD            -> identities, groups, logon and GPO scope
Synology NAS  -> SMB/share ACL and folder ACL enforcement
GPO/GPP       -> drive-letter mapping and endpoint client behavior
```

Do not use GPO as a workaround for missing NAS permissions. If a user cannot
access data, fix the NAS access model or stop the rollout.

## Preconditions

- The NAS is joined to the AD domain as a member file server only.
- The NAS can enumerate AD users and groups.
- DSM user home service is enabled after any domain join, rejoin, hostname
  change or domain-member rename.
- The pilot workstation is domain joined.
- The pilot ordinary user can log in to the domain.
- AD DNS and domain time are healthy on the pilot workstation.
- Legacy local Synology staff accounts are not used as the target auth model.
- Existing production shares are out of scope unless explicitly approved.
- The operator has an approved rollback path for GPO link changes.

## Guardrails

- Treat the NAS as production data storage.
- Delete-class operations against NAS data require separate immediate operator
  approval.
- A test file may be created only in the approved pilot home path.
- Removing a test file is a delete-class action unless the operator explicitly
  approves it as part of the pilot cleanup.
- Keep real NAS names, IPs, domain names, usernames, paths, ACL dumps and
  credentials outside this public runbook.

## Domain-Home Validation

From the pilot Windows workstation, log in as the ordinary domain user and open
the DSM-provided personal home share:

```text
\\<nas-host>\home
```

Create a clearly named test file in that location.

Expected behavior:

- the path opens without storing credentials on the endpoint;
- Windows uses the logged-in domain identity;
- the user can create and edit the test file;
- the file is owned by the domain user on the NAS;
- the file appears in a Synology domain-home path, not in a legacy local
  Synology user directory.

Synology may materialize domain homes under an internal domain-home directory
such as:

```text
<homes-root>/<domain-home-container>/<bucket>/<user-derived-directory>
```

Do not hard-code this internal path into GPO. Client mapping should use the
supported SMB home share.

## Isolation Validation

Before staff rollout, test with a second ordinary domain user.

Expected behavior:

- the second user can access their own `\\<nas-host>\home`;
- the second user cannot browse, create or edit files in the first user's
  private home;
- shared spaces remain governed by separate share/folder ACLs;
- no legacy local account is required for access.

If isolation fails, stop the rollout. Do not compensate by adding broad GPO
logic or credentials.

## Retiring Pilot GPO Artifacts

Pilot GPOs created for a specific user should be unlinked from active OUs after
the pilot has produced evidence.

Preferred cleanup:

1. Record the current GPO link state in operator-owned evidence.
2. Unlink the pilot GPO from the active OU.
3. Keep the pilot GPO object and SYSVOL contents temporarily as rollback or
   audit history.
4. Do not delete the pilot GPO until a separate cleanup decision exists.

Do not keep user-named pilot GPOs linked to staff OUs after moving to a staff
policy.

## Staff GPO/GPP Design

Create a neutral staff user-data GPO through the supported AD/GPO administration
path. Do not hand-build GPO objects directly in LDAP/SYSVOL.

Recommended first drive mapping:

```text
H: -> \\<nas-host>\home
```

The mapping must:

- use the current logged-in domain user;
- avoid stored credentials;
- avoid user-specific UNC paths;
- avoid persistent local credentials;
- target the staff user OU or approved staff security group;
- be easy to unlink if it causes a problem.

For GPP Drive Maps, prefer the simplest known-good structure first:

- action: `Update`;
- no `userName`, `password` or `cpassword` values;
- persistent mapping enabled if the operational model requires a stable drive
  letter across normal logon sessions;
- UNC path points to the supported NAS home share, not to an internal Synology
  domain-home path.

If a previous local profile has a stale persistent mapping to an old NAS name,
clean only that endpoint profile mapping as a separate bounded endpoint action.
Do not compensate by embedding credentials in GPO.

Shared-space drive mappings should be a later gate after ACL review:

```text
X: -> approved photo share
Y: -> approved video share
Z: -> approved organization share
```

Do not map legacy, archive, backup, restricted or unclear shares by default.

## Validation After GPO

On the pilot endpoint:

```powershell
gpupdate /force
gpresult /r
net use
```

Expected behavior:

- the target staff GPO applies to the user;
- `H:` maps to the user's personal NAS home;
- the mapping survives normal logoff/logon behavior according to the chosen GPP
  setting;
- no credentials are saved in the GPO or local scripts;
- no old pilot drive mappings remain.

If Group Policy applies but Drive Maps reports path-not-found, validate the NAS
home share before editing GPO again:

- DNS resolves the NAS member-server name;
- SMB port is reachable;
- DSM user home service is enabled;
- the logged-in domain user can open `\\<nas-host>\home` interactively.

A domain rejoin or hostname/domain-member rename can reset DSM home-share
settings. Treat that as a NAS service-state issue, not as evidence that GPO
should store credentials.

## Stop Conditions

Stop if:

- the NAS cannot resolve AD identities;
- DSM user home service is disabled or unclear after domain rejoin/rename;
- the home share prompts unexpectedly for credentials;
- a domain user lands in a legacy local Synology home directory;
- the pilot user can access another user's private home;
- a broad ACL rewrite appears necessary;
- DSM proposes an unclear permission conversion;
- GPO requires embedded credentials;
- endpoint logon becomes slow or unreliable and the cause is unclear;
- production users report unexpected SMB access changes.

## Rollback

Rollback should be configuration rollback, not data rollback:

1. Unlink the target staff user-data GPO.
2. Re-enable or relink the previous pilot state only if it is explicitly needed
   for diagnosis.
3. Leave NAS data and local user directories untouched.
4. Revalidate ordinary domain logon, DNS/time and SMB access.
5. Record a public-safe sign-off.

Do not delete user homes, test evidence or legacy directories as a rollback
shortcut.

## Evidence and Sign-Off

Public-safe sign-off may include:

- run class: `synology-nas-domain-home-gpo`;
- number of pilot users, not full user inventory;
- whether native domain home materialized;
- whether the test file was created in the domain home;
- whether isolation against another ordinary user was verified;
- whether pilot GPO was unlinked;
- whether target staff GPO is pending or applied;
- rollback snapshot reference without private payloads.

Do not include:

- real user passwords or temporary passwords;
- raw ACL dumps containing private identities if they are not redacted;
- complete NAS share inventory if it exposes private structure;
- private hostnames, IPs or domain names unless the artifact is private
  operator context.

## Activation Level

Current activation level: `L1 - public-safe runbook`.

No helper/script is added at this stage. A future helper may produce read-only
checks for domain-home materialization and GPO link state, but broad ACL or GPO
mutation must stay behind an explicit operator-approved gate.
