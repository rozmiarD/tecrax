# Network Security Device Management TLS Runbook

## Purpose

Use this runbook to remove legacy management-plane TLS without changing VPN,
traffic inspection, application-facing TLS or data-plane policy.

Management TLS labels are not necessarily minimum-version selectors. A device
may expose protocol sets such as:

- a compatibility set containing TLS 1.1, 1.2 and 1.3;
- TLS 1.2 only;
- TLS 1.3 only.

Never assume that selecting `TLS 1.2` preserves TLS 1.3. Prove the negotiated
protocols from every approved management path before saving.

## Preconditions

- Exact device identity and management address are verified.
- Running and startup configurations are equal.
- A fresh encrypted running/startup backup passes checksum and decrypt/read
  validation without plaintext written to operator storage.
- A separate authenticated SSH or console rollback session remains active.
- Every approved management client passes the currently required modern TLS
  handshakes before the change.
- VPN, SSL inspection, firewall, routing and application-facing TLS are
  explicitly outside the mutation scope.

## Safe Discovery

Prefer vendor documentation. If CLI completion is required:

- use tab completion without submitting the partial command;
- close the session with the partial line still unsubmitted;
- never use contextual `?` after a syntactically complete configuration
  prefix;
- immediately verify running against startup through a fresh session.

Record protocol-set semantics, not only option names.

## Canary

1. Enter the vendor's configuration rollback or transactional mode when
   supported.
2. Apply the candidate to running state only.
3. Do not save.
4. From every approved management path, test:
   - the legacy protocol is rejected;
   - every required modern protocol is accepted;
   - certificate and hostname validation behave as expected.
5. Verify SSH, read-only monitoring and centralized logging.
6. Save only if the complete desired protocol set passes.

If an option disables a required modern protocol, roll back immediately. Do not
accept a security or compatibility regression merely because the option name
looks correct.

## Default-Value Drift

On older firmware, removing an explicit setting may resolve to a newer compiled
default rather than the effective state loaded from an older startup
configuration. Therefore:

- compare negotiated behavior before and after rollback;
- compare running and startup configuration after rollback;
- if an explicit equivalent setting is required to restore behavior, document
  it and save only after an exact diff and full smoke;
- never use a reboot as an implicit rollback without separate authorization.

## Success

- The intended legacy protocol cannot negotiate from approved test clients.
- Every required modern protocol negotiates from every approved management
  path.
- Running equals startup.
- VPN, inspection, firewall and routing remain unchanged.
- Monitoring and centralized logging remain healthy.
- A post-change encrypted backup passes decrypt/read validation.

## Stop Conditions

Stop without saving when:

- the device cannot express the required protocol combination;
- the candidate removes a required modern protocol;
- rollback changes behavior or creates an unexpected default;
- running and startup do not reconcile;
- the rollback session or fresh backup is unavailable;
- the setting also affects VPN, inspection or data-plane TLS.
