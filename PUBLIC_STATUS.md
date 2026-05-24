# Tecrax Public Status

Tecrax is an **alpha local-fixture infrastructure-operations profile package** over GovEngine and SCLite.

## Current Truth

- Source version: `0.2.2a0`.
- Public release label: `0.2.2-alpha`.
- PyPI package: `tecrax==0.2.2a0` is the published current fixture-only alpha package.
- Dependency chain: `tecrax -> govengine>=0.11.0a0,<0.12 -> sclite-core>=0.8.0a0,<0.9`.
- Runtime posture: dry-run/local-fixture only.
- Public surface: `tecrax fixture-review --service demo-web`.

The `0.2.2-alpha` line is dependency/conformance synchronization only; it
keeps the fixture-only posture unchanged.

## Non-Claims

- no live infrastructure connection;
- no host inventory ownership;
- no credential, key-store, PKI, or KMS ownership;
- no carrier adapter implementation;
- no scheduler/storage/queue persistence ownership;
- no production operational readiness.
