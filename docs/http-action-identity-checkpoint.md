# HTTP action identity checkpoint

Status: accepted for Tecrax profile evolution; no runtime change in this document.

This checkpoint records how Tecrax may extend HTTP-based observations without moving
domain semantics into RExecOp or duplicating GovEngine/SCLite responsibilities.

## Verified current state

- RExecOp already has a domain-neutral `http_api` connector and validates profile-declared
  HTTP action shapes before backend I/O.
- RExecOp computes stable HTTP action-shape digests from method, path, query, body,
  unwrap/pagination, mutating flag and response-size bound.
- RExecOp binds HTTP shape digests into operation metadata and returns
  `action_contract_digest` from successful HTTP connector calls.
- Tecrax already declares `action_shapes` for:
  - `zabbix_api.read_zabbix_api_version`;
  - `portainer_api.read_portainer_status`.
- Tecrax does not use an AdGuard management API. The active AdGuard operation remains
  DNS resolution plus login-page reachability through `local_shell_readonly`.

## Ownership boundary

Tecrax owns:

- infrastructure operation vocabulary, intent IDs, workflow IDs and runbook references;
- connector contracts and allowed domain action shapes;
- the domain meaning of an observation, including non-claims and validation rules;
- normalized facts contracts such as Zabbix API reachability or Portainer reachability.

RExecOp owns:

- domain-neutral workflow planning, execution lifecycle and connector dispatch;
- generic action-shape validation and digest binding;
- fail-closed refusal when a configured HTTP action drifts from the profile contract;
- bounded connector output handling and redaction hooks.

GovEngine owns:

- admission, policy decisions, obligations/constraints and enforcement semantics;
- deciding whether an operation with a given bounded descriptor is allowed to run.

SCLite owns:

- canonical evidence, receipts, bundles and replayable truth artifacts;
- storing references and digests without interpreting infrastructure semantics.

## Decision

New Tecrax HTTP operations may be activated only when the operation can be represented as a
profile-owned immutable action shape. Runtime environments may provide endpoint location,
secret references, TLS CA references, timeout/retry values within accepted bounds and target
selection. Runtime environments must not redefine the domain action shape.

For active Tecrax HTTP actions, these fields are profile-owned:

- connector name and action name;
- HTTP method;
- path template;
- fixed query keys and values;
- fixed request body shape;
- unwrap/pagination shape;
- mutating flag;
- maximum response bytes;
- domain facts contract and validation rule.

For active Tecrax HTTP actions, these fields may be operator/environment-owned:

- base URL or base URL secret reference;
- authentication secret reference, only when a constrained read-only role is verified;
- TLS CA file secret reference;
- timeout and retry values, only within operation/runbook bounds.

If a future HTTP integration requires method/path/body/query/projection to be supplied by an
operator environment, it is not an active Tecrax operation. It must stay in an experimental,
fixture-only or audit-only path until the shape is made immutable in the profile.

## Activation gate for future HTTP slices

Before adding or widening an HTTP-based Tecrax observation, the implementation must show:

- an active intent with `modes: [read_only, dry_run]` and `side_effect_class: none`;
- a connector contract with explicit `action_shapes`;
- a facts contract with bounded schema, validator and non-claims;
- a validation rule that evaluates normalized facts, not raw API responses;
- a runbook that states what is observed and what is deliberately not observed;
- tests proving action-shape drift is refused before backend I/O;
- tests proving raw identifiers, tokens and oversized bodies do not enter facts,
  validation results or receipts;
- an operator sign-off artifact with no private IPs, hostnames, tokens or topology.

## Current service boundaries

Zabbix has two active layers: unauthenticated `apiinfo.version` reachability and
authenticated T4 count-only summaries for problem severity counts and host/agent
availability counts. Authenticated history, macro, user, configuration or raw object reads
are not active.

Portainer remains limited to unauthenticated `/api/status` through verified TLS. Endpoint,
stack, container, user, token and configuration reads are not active.

AdGuard remains limited to DNS resolution and login-page reachability. Management API reads
are not active without a verified read-only role or separately constrained adapter.

Docker remains limited to systemd service/socket observations. The Docker socket is not a
read-only boundary and must not be used as a shortcut for container inventory.

## Required negative vectors

Future HTTP slices must include negative vectors for:

- unknown HTTP action;
- configured method drift;
- configured path drift;
- configured body/query drift;
- unwrap or pagination drift that would expose broader data;
- mutating flag mismatch;
- missing profile action shape;
- oversized response refusal;
- secret redaction from echoed headers, bodies and error snippets;
- backend-not-called assertion when shape validation fails.

## Non-goals

This checkpoint does not introduce a Tecrax schema engine, policy engine, scheduler, target
catalog loader or SCLite evidence implementation. It does not authorize authenticated
management API discovery for Zabbix, AdGuard or Portainer.

## Next implementation checkpoint

The T5 checkpoint keeps AdGuard, Portainer and Docker expansion blocked unless a future
design checkpoint proves a constrained read-only boundary with negative vectors and
bounded facts.
