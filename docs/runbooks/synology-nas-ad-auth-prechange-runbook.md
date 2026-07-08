# Synology NAS AD Auth Pre-Change Runbook

This runbook prepares the controlled service window for integrating a Synology
NAS with Samba AD authentication for SMB file access.

It is a pre-change and pilot plan. It does not perform the domain join, rename
the NAS, rewrite ACLs, migrate local users or delete data.

## Scope

Allowed in this pre-change phase:

- confirm the approved target model;
- export and record current NAS configuration in an operator-owned location;
- capture read-only state for SMB, local users, groups, shares and relevant ACLs;
- define AD groups for the pilot;
- define stop, rollback and success criteria;
- prepare a one-user pilot for a single existing home directory.

Not allowed in this pre-change phase:

- delete, prune, purge or destructively overwrite NAS data;
- rename local NAS users;
- merge or delete local accounts;
- perform mass ACL rewrites;
- modify production shares beyond the explicitly approved pilot;
- store NAS, AD or domain join credentials in Git, GPO, scripts, chat or
  public sign-offs.

## Approved Architecture

The Synology NAS joins the AD domain only as an SMB/file-server member.

It must not become:

- a DNS server;
- a DHCP server;
- a domain controller;
- a source of identity truth.

Authority split:

```text
Samba AD    -> identity and domain groups
Synology NAS -> SMB/share ACL and folder ACL enforcement
GPO         -> client mapping and client configuration only
```

GPO must not be used as a substitute for data ACLs. GPO may map a drive letter
or configure client behavior, but access to data must still be enforced by the
NAS.

## Guardrails

- The NAS is high-risk because it stores production data.
- Deleting NAS data is forbidden unless the operator gives a separate,
  immediate and explicit delete-class confirmation.
- Existing local Synology accounts remain as fallback/legacy during the pilot.
- No local user rename, delete, merge or mass migration is allowed in the
  pilot.
- Existing production shares remain untouched unless explicitly included in a
  later approved change.
- Any credential used during the service window must stay in operator custody
  and must not be written to tracked files or public artifacts.

## Service Window

Record the approved service-window dates in the private roadmap or operator
context for the specific deployment.

Users must be informed before the window that SMB/file access can be temporarily
unavailable during the change.

SMB service restarts are allowed during the window if required by DSM or domain
join configuration. Restarting broader NAS services should be avoided unless
explicitly required and understood.

## Naming

Use AD groups for access, even for the first pilot. This validates the target
model and avoids hard-coding long-term access directly to users.

Recommended pilot group names:

```text
GG_<ORG>_NAS_Home_RW
```

Meaning:

- `GG` - global group;
- `<ORG>` - organization prefix;
- `NAS` - resource family;
- `Home` - user home resource family;
- `RW` - read/write user access;

Do not create administrative SMB-access groups for user home data. NAS
administration belongs to the NAS management plane, such as DSM or an approved
admin interface, not to per-share home ACL groups.

Do not create broad department-wide NAS groups during the first pass unless the
access model has been reviewed separately.

## Pilot Scope

Pilot user:

```text
<PilotUser>
```

Pilot data target:

```text
<HomesShare>/<PilotUser>
```

Pilot client mapping:

```text
<HomeDriveLetter>:
```

Out of scope for the first pilot:

- all non-pilot production shares;
- all other user homes;
- Offline Files;
- full Folder Redirection;
- local account migration;
- global ACL cleanup.

## Pre-Change Checklist

Before changing NAS authentication:

1. Confirm current NAS reachability and management access.
2. Confirm AD/DC health and time sync.
3. Confirm the pilot laptop can authenticate to the domain.
4. Export DSM configuration through the supported DSM path if available.
5. Capture read-only NAS state:
   - hostname and workgroup/domain state;
   - SMB global config;
   - share list;
   - local users;
   - local groups;
   - current `homes` settings;
   - top-level pilot home ownership and ACL summary;
   - package list relevant to SMB/auth;
   - current service status.
6. Confirm that no production file copy, cleanup or delete operation is part of
   the change.
7. Confirm the approved home access AD group exists or prepare its creation in
   AD.
8. Confirm rollback steps and stop criteria.

Store exports in an operator-owned location outside Git. Public sign-offs may
include paths and checksums, but must not include secret-bearing exports.

## Change Outline

During the service window:

1. Verify pre-change state is captured.
2. Create or verify the approved home access AD group.
3. Join Synology to the AD domain as a member/file server only.
4. Verify the NAS can resolve and enumerate AD users/groups.
5. Do not migrate local Synology accounts.
6. Do not rewrite ACLs globally.
7. Apply only the minimum pilot ACL change needed for the pilot home, if
   required.
8. Configure GPO/GPP drive mapping for the approved home drive letter only
   after NAS domain auth is confirmed.
9. Validate from the domain laptop.

## Validation

Success criteria:

- Synology sees the AD domain.
- Synology can find the pilot AD user and pilot AD group.
- Existing local NAS users and shares still exist.
- The pilot domain user maps the approved home drive letter from the domain
  laptop.
- The pilot domain user can create, edit and remove a test file in their own
  home directory.
- Another ordinary domain user cannot access the pilot user's home directory.
- Non-pilot shares are not modified.
- No delete-class operation was performed against production data.

Test-file handling:

- create a clearly named temporary test file only in the pilot home;
- remove that temporary test file only after confirming it was created by this
  test and only under operator-approved pilot scope;
- do not delete existing user data.

## Stop Conditions

Stop and rollback before wider testing if:

- Synology cannot join the domain cleanly;
- DNS/Kerberos/time errors appear and the cause is unclear;
- existing shares disappear or SMB access changes unexpectedly;
- DSM proposes a broad permission conversion that is not fully understood;
- the pilot requires changing ACLs outside the approved pilot home;
- a credential would need to be stored in GPO or a tracked script;
- any delete-class action would affect data outside the explicit pilot test
  file;
- production users report unexpected access loss outside the planned window.

## Rollback

Rollback is authentication/configuration rollback, not data rollback.

Preferred rollback:

1. Leave files untouched.
2. Revert Synology from AD member mode back to the previous workgroup/auth
   model.
3. Restore previous SMB/auth settings from the captured pre-change export or
   recorded values.
4. Remove or disable only pilot GPO/GPP mapping changes.
5. Validate legacy/local access paths.
6. Record public-safe rollback sign-off.

Do not delete local users, AD users, home directories or production data as a
rollback shortcut.

## Evidence and Sign-Off

Public-safe sign-off may include:

- run class: `synology-nas-ad-auth-prechange` or
  `synology-nas-ad-auth-pilot`;
- service-window date;
- target role: NAS SMB member;
- pilot user alias;
- pilot group names;
- share names in scope;
- validation result;
- rollback status;
- explicit non-claims.

Must not include:

- NAS admin credentials;
- domain join credentials;
- raw config exports containing secrets;
- private keys;
- SMB passwords, hashes or tokens;
- full private directory listings.

## Tecrax Artifact Decision

Current activation level: `L1 - public-safe runbook`.

This is not a deterministic Tecrax mutation yet. Synology domain join and ACL
changes are high-risk because the NAS stores production data. A helper may be
considered later only for read-only pre-change export and bounded validation,
not for broad ACL mutation, until multiple successful manual pilots define a
safe contract.
