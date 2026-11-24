# Invariants the schema should hold

A census of writers often turns up an invariant that every writer is *expected* to
respect and nothing enforces: one active profile per account and product, one open
invoice per customer, one current snapshot per device. The usual companion is a
helper that counts the violations and repairs them on every request.

**The repair helper is the defect, not the mitigation.** It reads the count, clears
all the flags, then sets one back. Two requests interleaving through that window both
observe a violation, both clear, both set — and the duplicate is back. The bug returns
under load, which is exactly when nobody is watching. Checking on every request is the
wrong shape for an invariant the storage engine can hold outright.

## The shape

A stored generated column mirrors the flag into a value that is unique only while it
matters, plus a unique key over the group and that column:

```sql
ALTER TABLE config_profiles
  ADD COLUMN active_slot TINYINT(1) AS (IF(is_active = 1, 1, NULL)) STORED,
  ADD UNIQUE KEY uq_one_active_per_product (account_id, config_type, active_slot);
```

Why it works: MySQL and MariaDB treat `NULL`s in a unique index as distinct. Any
number of inactive rows coexist (their slot is `NULL`); a second active row collides
on `1`. That gives a partial constraint without needing partial-index syntax, and
inactive history stays unlimited — which matters, because a product that can never
keep more than one historical row is a different product.

## Why this beats the alternatives

| Approach | Why it loses |
|---|---|
| Repair helper on every request | Races against itself; the window is the bug |
| Application lock around the repair | Serialises every request to protect one invariant; shared hosting has no daemon to hold the lock |
| `ORDER BY ... LIMIT 1` on the read sites | Picks a winner instead of preventing the ambiguity; leaves the data wrong and the next reader that forgets the `ORDER BY` broken |
| Trigger that deactivates siblings | Fires per row, is easy to bypass, and hides the write in a place nobody greps |
| Generated column + unique key | Every writer keeps working untouched |

**The decisive property is that writers need no change.** Every one already sets the
flag; the generated column follows. Twenty-two write sites across five files stayed
untouched, and a writer added next year is constrained without knowing the constraint
exists. An enforcement design that requires every caller to opt in is not enforcement.

## Install it idempotently, from the write path

Put the install in a function called by the save path, not in a migration file the
deployer must remember. Match whatever self-healing pattern the repo already uses —
an inline `SHOW TABLES LIKE` guard before `CREATE TABLE` is the common one.

Order inside the function matters:

1. **Return immediately if the column and key already exist.** This is the path a
   normal request takes, so it must be the cheapest one. Measure it; a check that
   costs a metadata round trip on every write is a new problem.
2. **Repair pre-existing duplicates first.** The key cannot be created while they
   exist. Keep the newest row per group using the same rule the old helper used, so
   the fix does not introduce a winner the product would disagree with.
3. **Add the column, then the key.** Two statements, because a combined `ALTER`
   fails differently across versions and you want to know which half failed.

Log what the repair cleared, with the group and the row kept. A silent repair on a
production database is a data change nobody can audit afterwards.

## Measure before shipping

Run it against a production-shaped fixture, not an empty table: many accounts, several
products, real profile history, and a deliberate population of duplicate groups.

Report all of these:

- **Groups repaired and rows deactivated.** A count that differs from the number of
groups means one group had more than two.
- **Rows deleted — which must be zero.** Only the flag clears; the row and its data
  stay. If your repair deletes, it is a data-loss path wearing a constraint's clothes.
- **First-run cost and steady-state cost.** The first is a one-time `ALTER` plus the
  repair; every later call is the existence check.
- **The invariant holds after** — one active row per group, exactly.
- **Inactive rows still unlimited**, and a brand-new group's first active row allowed.

## Then leave the read sites alone

With the constraint in place there is exactly one active row per group, so a bare
`WHERE is_active = 1` is unambiguous. Adding `ORDER BY` to every read site is diff
churn that changes no behaviour, and it hides the fact that the ambiguity was fixed at
the source. Resist it, and say in the plan why the reads were left untouched so a
later reviewer does not read the omission as an oversight.

## Verify on the versions that matter

Generated-column semantics moved between MariaDB 10.x and 11.x. A local 10.4 result is
not evidence for an 11.8 host. Probe the exact DDL on the version production runs —
create the table, activate one row, try to activate a second and require the duplicate
key error, insert inactive rows and require success — before trusting the suite's green
run on a different version.
