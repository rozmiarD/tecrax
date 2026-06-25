# Tecrax domain contracts

Tecrax facts use static `FactsContractSpec` definitions in `tecrax.contracts`. They are
small profile-owned payload contracts inside SCLite canonical observation envelopes; they
are not a schema service, registry daemon, storage layer, DSL, or replacement for SCLite.

Every active intent declares profile-owned `facts_contract`. A result separates:

- `contract`: stable id and version;
- `scope`: requested, observed and deliberately not observed fields;
- `coverage`: complete, partial or blocked plus bounded blockers;
- `assessment`: healthy, degraded, unhealthy or unknown;
- `non_claims`: facts the operation explicitly does not establish.

Malformed facts, raw connector output and payloads above 16 KiB are rejected before Tecrax
builds a SCLite observation. A negative health assessment remains a valid observation.

## Reference contract: basic host inventory v1

`collect_basic_host_inventory` is the first T1 reference slice:

- intent declaration: `facts_contract: tecrax.basic_host_inventory@1.0`;
- domain capability: `tecrax.host.basic_inventory.v1`;
- static schema artifact: `src/tecrax/schemas/basic_host_inventory.v1.schema.json`;
- typed model/builder: `BasicHostInventoryV1` and `build_basic_host_inventory_v1`;
- pure validator: `validate_basic_host_inventory_v1`.

The contract covers only bounded read-only facts: target label, OS release fields, kernel,
hostname, uptime string, load averages, root filesystem summary from `df -P /`, and memory
summary from `free -m`. It explicitly does not claim package inventory, users, processes or
network listeners.

Compatibility policy: additive optional fields may stay within `1.x`; removing fields,
changing meaning or changing required keys requires a new major contract version and golden
N-1 vectors. RExecOp executes the workflow, GovEngine governs it, and SCLite owns the
canonical envelope and evidence lifecycle.
