# DNS authority checkpoint runbook

This runbook records the DNS authority decision before Samba AD DC and AdGuard
Home are deployed.

It is not an active Tecrax profile intent and does not add a DNS connector. It
is an operator-owned architecture checkpoint used to avoid split-brain DNS,
broken domain joins, Kerberos/SRV lookup failures and forwarding loops.

## Scope

The checkpoint covers:

- authority model for AD DNS and filtering DNS;
- AD-joined client DNS flow;
- non-AD device DNS flow;
- forwarding and conditional-forwarding rules;
- loop prevention;
- public-safe sign-off.

It does not deploy Samba AD DC, deploy AdGuard, modify DHCP, create DNS zones,
or migrate clients.

## Public and Private Boundary

Safe in public docs and sign-offs:

- generic roles: AD DNS, filtering DNS, upstream DNS;
- generic flows for AD and non-AD clients;
- reserved-service intent when the operator explicitly approves it;
- non-claims and stop conditions.

Must remain outside Git and public sign-offs:

- real domain names;
- private subnet details beyond explicitly approved reservations;
- host fingerprints, key paths, credentials and API tokens;
- full DHCP scopes, VLANs and static lease inventories;
- raw resolver logs or client inventories.

## Decision

Approved default model:

```text
AD-joined users/devices
  -> AD DNS
  -> AdGuard filtering DNS
  -> upstream internet DNS

Non-AD / IoT / guest / appliances
  -> AdGuard filtering DNS
  -> upstream internet DNS

AdGuard conditional local-domain lookup, if needed
  -> AD DNS only for the AD domain and selected reverse zones
```

The reserved filtering DNS service address for AdGuard is operator-approved
private topology material. It may be referenced in private deployment plans. Do
not generalize it into public examples unless the operator explicitly allows it.

## Authority Rules

### AD DNS

AD DNS is authoritative for the AD domain and AD service records:

- domain zone;
- `_msdcs` zone;
- Kerberos and LDAP SRV records;
- domain-controller discovery records;
- AD-managed reverse zones when selected.

AD-joined clients must use AD DNS as their DNS resolver. Do not configure public
DNS or filtering DNS as a fallback resolver on AD clients unless a separate
failure-mode design has been approved.

### AdGuard

AdGuard is filtering/forwarding DNS, not the authority for the AD domain.

AdGuard may:

- filter internet DNS requests;
- forward to selected upstream resolvers;
- conditionally forward the AD domain to AD DNS;
- conditionally forward selected reverse zones to AD DNS.

AdGuard must not become the primary authority for AD SRV records.

### Non-AD clients

Non-AD clients may use AdGuard directly. This includes guest, IoT, appliances and
devices that are intentionally outside domain management.

If those clients need to resolve the AD domain, AdGuard should forward only the
AD domain and selected reverse zones to AD DNS.

## Loop Prevention

Allowed:

```text
AD DNS -> AdGuard -> upstream internet DNS
AdGuard -> AD DNS only for AD domain / selected reverse zones
```

Not allowed:

```text
AD DNS -> AdGuard -> AD DNS for all queries
AdGuard -> AD DNS -> AdGuard for the same domain class
Clients with AD DNS primary and unrelated public DNS fallback
```

Every forwarding rule must have a bounded domain class. "Everything forwards
back to the other resolver" is a stop condition.

## DHCP Policy Shape

Public-safe policy:

- AD-managed client scopes: DNS resolver is AD DNS.
- Non-AD/guest/IoT scopes: DNS resolver is AdGuard.
- DHCP changes are performed only after Samba AD DNS and AdGuard behavior are
  validated.

Exact scopes, reservations and leases remain private operator material.

## Validation

Before deploying clients against the model, validate:

- AD DNS resolves AD SRV records locally;
- AD DNS forwards non-local names to AdGuard;
- AdGuard resolves internet names through upstream;
- AdGuard forwards only the AD domain and selected reverse zones to AD DNS;
- no forwarding loop exists;
- AD clients can join/authenticate without using AdGuard as their direct DNS;
- non-AD clients can resolve internet names through AdGuard.

## Stop Conditions

Stop before Samba/AdGuard deployment if any of these are true:

- AD domain name is undecided;
- AdGuard would be authoritative for AD records;
- AD clients would receive AdGuard or public DNS as fallback without a deliberate
  failure-mode design;
- forwarding rules create a loop;
- DHCP ownership is unclear;
- validation would require exposing domain secrets, credentials or private
  topology.

## Sign-Off Shape

Use `docs/operator-signoff-template.md` and include:

- date;
- run class: `dns-authority-checkpoint`;
- AD DNS authority decision;
- AdGuard filtering/forwarding decision;
- AD-client resolver policy;
- non-AD resolver policy;
- loop-prevention summary;
- explicit non-claims.

Non-claims:

- no Samba AD DC deployment;
- no AdGuard deployment;
- no DHCP migration;
- no production client migration;
- no secret or topology disclosure.

## Next Gate

After this checkpoint, write the Samba AD DC deployment runbook and deploy the
domain DNS authority before finalizing AdGuard filtering behavior.
