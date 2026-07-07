# PKI certificate lifecycle planning runbook

This runbook covers the planning baseline for future internal certificate
issuance, renewal, revocation and trust distribution.

It is intentionally a planning runbook. It does not generate root CA material,
intermediate CA material, private keys, CSRs, certificates, CRLs, trust stores
or service HTTPS configuration.

## Scope

The planning baseline covers:

- future internal FQDN/SAN naming rules;
- certificate request intake shape;
- issuance approval boundaries;
- renewal and expiry windows;
- revocation decision shape;
- trust-root distribution plan for Windows and Linux targets;
- private certificate inventory template;
- public-safe sign-off shape.

It does not cover:

- OpenSSL production policy files;
- CA private keys or passphrases;
- root or intermediate generation;
- certificate issuance;
- trust-root deployment;
- service HTTPS migration;
- automatic certificate rotation;
- compliance sign-off.

## Public And Private Boundary

Safe in public docs and sign-offs:

- lifecycle phases;
- approved field names for a private certificate registry;
- role and approval model;
- renewal/revocation concepts;
- explicit non-claims.

Must remain outside Git and public sign-offs:

- CA private keys, passphrases and recovery material;
- generated CSRs containing sensitive topology or service details;
- issued certificates if they expose private names that are not approved for
  public docs;
- private key paths, keystores, truststores and service credentials;
- exact internal certificate inventory unless the operator approves redaction.

## Naming And Request Baseline

Every future certificate request should define:

- service alias;
- owner role;
- environment;
- intended FQDN;
- SAN list;
- target service or endpoint class;
- expected validity class;
- renewal owner;
- revocation contact;
- distribution target.

Rules:

- prefer stable service aliases and internal DNS names over raw IP addresses;
- include SANs explicitly; do not rely on Common Name only;
- do not issue broad wildcard certificates as the first internal baseline;
- do not reuse one private key across unrelated services;
- do not issue certificates for unknown or unowned services;
- do not publish private SAN lists in public docs unless they are already
  approved for disclosure.

## Private Certificate Registry Shape

The private operator registry may use this shape:

```yaml
version: 1
policy:
  model: private_inventory_no_secrets
certificates: []
```

Future entries may use these fields:

```yaml
- id: example-service-internal-tls
  service_alias: example-service
  owner_role: IT administrator
  environment: internal
  fqdn: example.internal.invalid
  san_refs:
    - dns:example.internal.invalid
  issuer_ref: pki01-intermediate
  validity_days: 397
  status: planned
  private_key_custody: service-local-or-approved-secret-store
  renewal_window_days: 30
  revocation_contact_role: IT administrator
  distribution_targets:
    - linux_trust_store
  notes:
    - Template only. Do not store private keys or passphrases here.
```

The registry must not contain private keys, passphrases, admin tokens, vault
exports or raw CA material.

## Issuance Planning

Before issuing any certificate, confirm:

- service owner and purpose;
- FQDN and SANs are correct;
- target service can be restored from backup;
- private key custody is defined;
- deployment rollback path exists;
- monitoring can detect expiry and service TLS failure;
- certificate is recorded in the private registry.

Issuance should remain manual until the hardening phase defines approved
OpenSSL policy files, CSR templates and deterministic wrappers.

## Renewal Planning

Recommended initial policy:

- record `not_after` for every issued certificate;
- warn before expiry through the private inventory/check layer;
- renew in a defined maintenance window;
- validate service after replacement;
- keep rollback material only under the approved custody model.

Do not automate renewal until:

- the private registry is reliable;
- service-specific deployment steps are known;
- rollback is tested;
- secrets never pass through AI, repo or public logs.

## Revocation Planning

Revocation must be possible when:

- private key compromise is suspected;
- service ownership changes;
- service is decommissioned;
- SAN/FQDN was issued incorrectly;
- certificate was generated outside the approved process.

The final revocation procedure belongs to hardening. This planning runbook only
requires that every planned certificate has a revocation contact and registry
entry.

## Trust Distribution Planning

Windows domain endpoints:

- preferred future path: AD/GPO trust-root distribution;
- start with a small pilot OU before broad rollout;
- verify trust store state and rollback path;
- do not distribute trust roots before CA custody is approved.

Linux VM/CT hosts:

- preferred future path: package or config-management controlled trust store
  update;
- validate trust update on one non-critical host first;
- record host class and rollback method;
- avoid ad hoc copying of trust roots without inventory.

Network devices and appliances:

- defer until device-specific import/export behavior is known;
- keep device credentials outside Tecrax and AI;
- record manual import evidence without private key material.

## Stop Conditions

Stop before issuance planning moves into execution if:

- CA custody is not approved;
- offline/root recovery is not defined;
- private key handling is unclear;
- backup/restore status of target service is unknown;
- SAN/FQDN ownership is ambiguous;
- deployment would require exposing secrets to AI or public docs;
- rollback path does not exist.

## Sign-Off Shape

Use `../operator-signoff-template.md` and include:

- date;
- run class: `pki-certificate-lifecycle-planning`;
- registry template status;
- planned target classes;
- trust distribution model;
- open hardening gates;
- explicit non-claims.

Non-claims:

- no root CA;
- no intermediate CA;
- no private keys;
- no CSRs;
- no issued certificates;
- no trust-root deployment;
- no service HTTPS migration;
- no compliance certification.

## Tecrax Artifact Target

Current target: `L1` public-safe planning runbook plus private empty inventory
template.

Future candidates:

- `L3` read-only certificate inventory and expiry summaries;
- `L3` trust-root distribution status summaries;
- `L4` issuance/renewal wrappers only after custody, policy and rollback gates
  are approved during hardening.
