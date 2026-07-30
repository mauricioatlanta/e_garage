# eGarage Contract Registry

This directory is the authoritative source of truth for all integration contracts
in the eGarage platform.

## What is a Contract?

A Contract is the formal agreement that governs how two subsystems of eGarage
exchange information. No subsystem may consume data from another without a
registered, stable contract. No subsystem may produce data for another without
being listed as a publisher.

**Principle of Autonomy**: No subsystem controls another. Subsystems cooperate
exclusively through public integration contracts. This means ERP Core does not
give permission to Commerce Engine — it publishes contracts that Commerce Engine
may consume.

**Corollary**: Every subsystem must be architecturally separable. If a subsystem
disappeared tomorrow, only its contracts would break — not the internals of
other subsystems.

---

## Taxonomy

| Type | Description | Examples |
|------|-------------|---------|
| **A — Truth** | Single write authority. All others read. | Product Knowledge, Stock, TaxPolicy, Identity |
| **B — Capability** | Declares what is possible, not what happened. | Capability, Payment Registry, Localization |
| **C — Behavioral** | Stateless computation. Given inputs, produces outputs. | Pricing, Promotion, Search |
| **D — Session** | Transient state with no permanent owner. | Cart, Session |
| **E — Event** | Immutable fact that something occurred. | Order Events, Notification, Analytics, Audit |
| **F — Infrastructure** | Platform-level concerns shared by all subsystems. | Media, Storage, Cache, Index |

### Event sub-types (Type E)

| Sub-type | Naming rule | Examples |
|----------|-------------|---------|
| Domain Event | Past tense from the business perspective | `order.placed`, `payment.confirmed`, `stock.depleted` |
| Technical Event | Past tense from the system perspective | `cache.invalidated`, `index.rebuilt`, `media.resized` |

Rule: if you are unsure which sub-type an event belongs to, ask — "Would the
workshop owner care about this event?" If yes, it is a Domain Event.

---

## Naming Convention

```
{domain}.{contract-name}.{version}

Examples:
  catalog.product-knowledge.v1
  inventory.stock.v1
  commerce.order.v1
  identity.profile.v1
  platform.localization.v1
```

The `{domain}` prefix is the bounded context that *owns and versions* the
contract, not necessarily the consumer. Sub-domains are preferred over
top-level domains (`erp.catalog` → `catalog`, not `erp`).

---

## Contract Registry

| Contract ID | Category | Publisher | Consumers | Status |
|-------------|----------|-----------|-----------|--------|
| `catalog.product-knowledge.v1` | Truth | `erp.catalog` | `commerce.engine`, `analytics` | Draft |
| `inventory.stock.v1` | Truth | `erp.inventory` | `commerce.engine` | Draft |
| `tax.policy.v1` | Truth | `erp.tax-engine` | `commerce.engine` | Draft |
| `identity.profile.v1` | Truth | `identity` | `erp.core`, `commerce.engine` | Draft |

---

## Rules

1. Every contract starts with `status: draft`.
2. No contract may be consumed in production before reaching `status: stable`.
3. A breaking change always requires a new major version (`v2`).
4. Every new contract must be accompanied by an ADR (see `/docs/adr-template.md`).
5. The `consumers` list is exhaustive — unlisted consumers are unauthorized.
6. Only the declared `write_authority` may write data covered by a Truth contract.
7. No implementation may begin until the contract's `pending_decisions` list is empty.

---

## Breaking Change Policy

| Change | Breaking | Requires |
|--------|----------|---------|
| Add optional field | No | patch version (`1.0.x`) |
| Add authorized consumer | No | patch version |
| Remove any field | **Yes** | major version + deprecation period |
| Change field type | **Yes** | major version |
| Change direction (Pull → Event) | **Yes** | major version + migration plan |
| Strengthen a guarantee | **Yes** | major version |
| Relax a guarantee | **Yes** | major version (consumers depend on it) |

---

## Adding a New Contract

1. Write an ADR (see `/docs/adr-template.md`) answering the seven questions.
2. Copy `meta-contract.yaml` and fill in all required fields.
3. Create the payload schema in `schemas/{contract-id}.schema.json`.
4. Add a row to the Registry table in this README.
5. Submit for review. Do not set `status: stable` until reviewed and all
   `pending_decisions` are resolved.

---

## Directory Structure

```
contracts/
├── README.md                                      ← registry index (this file)
├── meta-contract.yaml                             ← template every contract must follow
├── registry/                                      ← one file per registered contract
│   ├── catalog.product-knowledge.v1.yaml
│   ├── inventory.stock.v1.yaml
│   ├── tax.policy.v1.yaml
│   └── identity.profile.v1.yaml
└── schemas/                                       ← JSON Schema for each contract payload
    ├── meta-contract.schema.json
    ├── catalog.product-knowledge.v1.schema.json
    ├── inventory.stock.v1.schema.json
    ├── tax.policy.v1.schema.json
    └── identity.profile.v1.schema.json
```
