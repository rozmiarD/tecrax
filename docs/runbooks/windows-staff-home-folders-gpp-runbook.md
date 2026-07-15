# Windows staff home folders through GPP

## Purpose and boundary

Use Group Policy Preferences Folders to create the standard staff directories
`Pulpit`, `Dokumenty`, and `Pliki` below the supported per-user SMB home share.
This runbook does not configure Folder Redirection, Offline Files, Synology
internals, share permissions, or NAS storage. It must not delete, move, replace,
or overwrite an existing directory or user data.

The owning policy also maps the user's home and authorized shared resources.
Preserve those Drive Maps settings byte-for-byte while adding the Folders
extension.

## Required semantics

- Use only the supported path `\\nas01\home` and its three child paths.
- Use exactly three `Create` actions (`action="C"`).
- Run each item in the logged-on user context (`userContext="1"`).
- Leave created directories in place when policy stops applying
  (`removePolicy="0"`).
- Never embed a username, password, `cpassword`, or an internal NAS path.
- Treat an existing `Pliki` directory and all of its contents as protected data.

The Group Policy client-side extension pairs are:

- Drive Maps: `{5794DAFD-BE60-433F-88A2-1A31939AC01F}` and
  `{2EA1A81B-48E5-45E9-8BB7-A6E3AC170006}`.
- Folders: `{6232C319-91AC-4931-9385-E70C2B099F0E}` and
  `{3EC4E9D3-714D-471F-88DC-4DD4471AAB47}`.

## Preflight

1. Confirm the endpoint identity, current console user, domain membership, DNS,
   and access to the supported SMB name.
2. Confirm the GPO GUID, link scope, current LDAP version, current GPT version,
   user extension metadata, and the hashes of existing Drive Maps files.
3. Confirm the policy is scoped only to the intended pilot OU and user.
4. Validate the proposed `Folders.xml` with the fail-closed operator validator.
5. Take a native GPO backup immediately before mutation. Supply an explicit
   persistent temporary/backup directory; do not rely on an ephemeral default.
6. Record the backup path, pre-change version, payload hashes, and ACL reference.

Stop if identity, scope, backup, version equality, payload validation, or access
is uncertain. Stop if the operation would require changing NAS configuration or
touching user data.

## Apply

1. Install only the validated `Folders.xml` in the user-side Preferences tree.
2. Preserve the existing Drive Maps payload and its hash.
3. Add the Folders extension pair without removing or reordering unrelated
   extension metadata.
4. Increment only the user half of the GPO version and keep LDAP and GPT versions
   equal.
5. Apply directory and file ACLs by comparison with the neighboring, working
   Drive Maps extension. Do not broaden access.

Use an exact, pre-version-bound helper for the live mutation. Such a helper is a
single-use transaction: after success or rollback, retain the validator and
payload, but do not reuse a script whose expected version and backup are stale.

## Validation

Validate all of the following before declaring success:

- exact `Folders.xml` readback and the three `Create` actions;
- no forbidden paths or stored credentials;
- unchanged Drive Maps payload hash;
- correct extension pairs and matching LDAP/GPT user versions;
- target SYSVOL ACLs matching the known-good neighboring preference files;
- `gpupdate` and `gpresult` for the interactive pilot user;
- Group Policy Operational events showing successful Drive Maps and Folders
  processing with no GPP errors;
- user confirmation that the authorized drives and all three home directories
  are visible after a fresh sign-in or reboot.

A `gpupdate` does not refresh every access token or reconnect every persistent
drive. If some mappings remain disconnected while policy processing succeeds,
inspect the user's effective groups and session first. A logoff/sign-in or reboot
may be the correct bounded refresh. Do not delete/recreate mappings or enter
alternate credentials before that diagnosis.

A global SYSVOL ACL check may expose drift in an unrelated GPO. Record that as a
separate, backed-up remediation item; do not hide or repair unrelated policy
state inside this change.

## Rollback

Restore the recorded pre-change GPO metadata and payload, or remove only the new
Folders extension payload and metadata. Verify the original version, extension
metadata, Drive Maps hash, and ACLs after rollback.

Rollback must never remove any directory created by the policy and must never
delete or alter user files. NAS-side changes are not part of this rollback.
