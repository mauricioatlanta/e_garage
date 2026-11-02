# Architecture Decision Records — eGarage Platform

An ADR (Architecture Decision Record) is the formal document that authorizes an
architectural decision in eGarage. No contract may move from `draft` to `stable`
until every ADR listed in its `pending_decisions` field is in `Accepted` state.

---

## States and Transitions

```
Proposed → Accepted      (decision reviewed and approved)
Proposed → Rejected      (decision reviewed and discarded)
Accepted → Superseded    (replaced by a newer ADR)
Accepted → Deprecated    (the concern no longer applies)
```

**A contract may not be consumed in production if any of its pending ADRs
are in Proposed, Rejected, or Superseded state.**

Only `Accepted` unblocks implementation.

---

## Dependency Graph

```
ADR-001 (Attribute Schema)
    └── ADR-002 (Publication Trigger)
              └── catalog.product-knowledge.v1 → stable

ADR-004 (Multi-warehouse)
    └── ADR-003 (Stock Reservation)
              └── inventory.stock.v1 → stable

ADR-005 (Tax Calculation Authority)
    └── tax.policy.v1 → stable

ADR-006 (Identity Linkage Key)
    └── ADR-007 (Guest Identity)
              └── identity.profile.v1 → stable
```

ADR-004 must precede ADR-003 because the stock reservation policy depends on
whether stock is tracked as an aggregate or distributed across warehouses.

---

## Recommended Execution Order

| Block | ADR | Reason |
|-------|-----|--------|
| A — Catalog | ADR-001 | Foundation: defines attribute typing before publication |
| A — Catalog | ADR-002 | Depends on ADR-001 for what gets published |
| B — Inventory | ADR-004 | Foundation: defines warehouse model before reservation |
| B — Inventory | ADR-003 | Depends on ADR-004 for reservation scope |
| C — Tax | ADR-005 | Independent of other blocks |
| D — Identity | ADR-006 | Foundation: defines linkage key before guest model |
| D — Identity | ADR-007 | Depends on ADR-006 for identity persistence rules |

---

## ADR Index

| ADR | Title | Status | Contracts Affected |
|-----|-------|--------|--------------------|
| [ADR-000](ADR-000-meta-contract-evolution.md) | Meta-Contract Evolution: Message Types, Interaction, Transport | **Accepted** | **todos** |
| [ADR-001](ADR-001-attribute-schema.md) | Attribute Schema | Proposed | `catalog.product-knowledge.v1` |
| [ADR-002](ADR-002-catalog-publication-trigger.md) | Catalog Publication Trigger | Proposed | `catalog.product-knowledge.v1` |
| [ADR-003](ADR-003-stock-reservation.md) | Stock Reservation | Proposed | `inventory.stock.v1` |
| [ADR-004](ADR-004-multi-warehouse.md) | Multi-warehouse Strategy | Proposed | `inventory.stock.v1` |
| [ADR-005](ADR-005-tax-calculation-authority.md) | Tax Calculation Authority | Proposed | `tax.policy.v1` |
| [ADR-006](ADR-006-identity-linkage-key.md) | Identity Linkage Key | Proposed | `identity.profile.v1` |
| [ADR-007](ADR-007-guest-identity.md) | Guest Identity | Proposed | `identity.profile.v1` |

---

## Criteria for Moving an ADR to Accepted

1. All sections of the ADR template are filled — no placeholder text.
2. The decision has been reviewed by at least one architect (not the original author).
3. All options considered are documented, including the rejected ones.
4. The acceptance criteria (section 12) are specific and testable.
5. No conflicting Accepted ADR exists.

---

## How to Write a New ADR

1. Take the next available number from this index.
2. Create the file: `ADR-NNN-short-title.md`.
3. Fill in all 14 sections of the template.
4. Set `Estado: Proposed`.
5. Add the ADR to the index table above.
6. Reference the ADR in the `pending_decisions` field of all affected contracts.
7. Do not begin implementation until the ADR reaches `Accepted`.
