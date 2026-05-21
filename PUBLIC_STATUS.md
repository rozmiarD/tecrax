# Tecrax Public Status

Tecrax is an **alpha local-fixture infrastructure-operations profile package** over GovEngine and SCLite.

## Current Truth

- Source version: `0.2.0a0`.
- Public release label: `0.2.0-alpha`.
- Dependency chain: `tecrax -> govengine>=0.10.1a0,<0.11 -> sclite-core>=0.6.0a0,<0.7`.
- Runtime posture: dry-run/local-fixture only.
- Public surface: `tecrax fixture-review --service demo-web`.

## Non-Claims

- no live infrastructure connection;
- no host inventory ownership;
- no credential, key-store, PKI, or KMS ownership;
- no carrier adapter implementation;
- no scheduler/storage/queue persistence ownership;
- no production operational readiness.
