# Reference Datasets

All fixtures are synthetic, deterministic and safe to commit publicly. They are deliberately small enough to inspect by eye.

| Scenario | Pattern | Source shape | Main lesson |
|---|---|---|---|
| country reference | P01 | complete snapshot | current replacement, snapshot fidelity |
| legacy customers | P02 | ordered complete snapshots | snapshot-derived SCD2 + absence delete |
| CRM customers | P07 | watermark observations | lookback/redelivery + raw Bronze + soft delete |
| sales customers | P10 | normalized Debezium/full CDC | delivery identity vs source order + SCD2 |
| commerce orders | P12 | domain events | event identity, canonical events, quarantine |

## Expected change stories

### P01 country

The four-row country snapshot is authoritative in full. Re-running the same snapshot must not create duplicate current-state rows.

### P02 legacy customer

- snapshot 1: C001 and C002 exist;
- snapshot 2: C001 changes segment/status, C002 is unchanged, C003 is inserted;
- snapshot 3: C001 changes name, C002 disappears (delete by absence), C003 changes status.

The expected history file expresses logical snapshot intervals. Physical Databricks AUTO CDC history columns may use `__START_AT`/`__END_AT`; certification maps those physical fields to these logical expectations.

### P07 CRM customer

The observation stream contains intentional overlap/redelivery for C001. Latest authoritative source versions determine Silver state; C002 eventually becomes soft-deleted. Delivery metadata must not be mistaken for business/source identity.

### P10 sales CDC

The normalized feed contains create/read/update/delete operations with Kafka coordinates and source ordering columns. Baseline delivery identities are unique. Failure fixtures add duplicate and out-of-order delivery separately so happy-path and recovery evidence stay distinguishable.

### P12 order events

Baseline events have unique event IDs. Failure fixtures include a duplicate business event and an unknown event type to exercise deduplication/quarantine semantics.

## Scale testing

Tiny deterministic fixtures prove semantics, not performance. Large-volume/load certification should be generated separately and must preserve the same expected invariants rather than replacing these human-readable fixtures.
