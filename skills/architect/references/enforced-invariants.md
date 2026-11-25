# Invariants the schema should hold

A census of writers often turns up an invariant that every writer is *expected* to
respect and nothing enforces: one active profile per account and product, one open
invoice per customer, one current snapshot per device. The usual companion is a
helper that counts the violations and repairs them on every request.

**The repair helper is the defect, not the mitigation.** It reads the count, clears
all the flags, then sets one back. Two requests interleaving through that window both
observe a violation, both clear, both set, and the duplicate is back. The bug returns
under load, when nobody is watching. An invariant that many write sites must keep
belongs in the schema, where the storage engine holds it for all of them.

## The shape

The rule is "at most one row per group where a condition holds". Rows outside the
condition stay unlimited: inactive history, closed invoices, old snapshots. The
examples use a `profiles` table grouped by `(account_id, kind)` with an `is_active`
flag.

### Postgres and SQLite: partial unique index

Both engines index only the rows a `WHERE` clause selects:

```sql
CREATE UNIQUE INDEX uq_one_active_profile
  ON profiles (account_id, kind)
  WHERE is_active;
```

SQLite takes the same statement; with an integer flag, write the predicate as
`WHERE is_active = 1`. A second active row in a group fails with a unique violation.
Inactive rows are not in the index at all.

### MySQL and MariaDB: generated-column slot

Neither engine has partial indexes. Add a generated column that is non-NULL only for
the rows the rule covers, and put a unique index on the group plus that column:

```sql
ALTER TABLE profiles
  ADD COLUMN active_slot TINYINT(1) AS (IF(is_active = 1, 1, NULL)) STORED,
  ADD UNIQUE KEY uq_one_active_profile (account_id, kind, active_slot);
```

Both engines treat `NULL`s in a unique index as distinct. Any number of inactive rows
coexist because their slot is `NULL`; a second active row collides on `1`.

## Why this beats the alternatives

| Approach | Why it loses |
|---|---|
| Repair helper on every request | Races against itself; the window is the bug |
| Application lock around the repair | Serialises every request to protect one invariant, and needs a lock service every deployment can reach |
| `ORDER BY ... LIMIT 1` on the read sites | Picks a winner instead of preventing the ambiguity; leaves the data wrong and the next reader that forgets the `ORDER BY` broken |
| Trigger that deactivates siblings | Fires per row, is easy to bypass, and hides the write where no search for the flag finds it |
| Partial unique index, or generated column plus unique key | Every writer keeps working untouched |

**The decisive property is that writers need no change.** Every one already sets the
flag; the index or the generated column follows it. A writer added next year is
constrained without knowing the constraint exists. An enforcement design that requires
every caller to opt in is not enforcement.

## Install it idempotently

Install it the way the repo already changes its schema. With a migration runner, it
is one migration. Where the repo creates its schema on demand (a guard before
`CREATE TABLE` on the write path is the common pattern), put the install in a function
that path calls.

Order matters:

1. **Return immediately if the constraint already exists.** On an on-demand install
   this is the path a normal request takes, so it must be the cheapest one. Measure
   it; a check that costs a metadata round trip on every write is a new problem.
   Postgres and SQLite accept `CREATE UNIQUE INDEX IF NOT EXISTS`.
2. **Repair pre-existing duplicates first.** The engine refuses to build the index
   while they exist. Keep one row per group by the same rule the old helper used, so
   the fix does not introduce a winner the product would disagree with.
3. **On MySQL and MariaDB, add the column, then the key.** Two statements, because a
   combined `ALTER` fails differently across versions and you want to know which half
   failed.

Log what the repair cleared, with the group and the row kept. A silent repair on a
production database is a data change nobody can audit afterwards.

## Measure before shipping

Run it against a production-shaped fixture, not an empty table: many groups, real
row history, and a deliberate population of duplicate groups.

Report all of these:

- **Groups repaired and rows deactivated.** A count that differs from the number of
  groups means one group had more than two.
- **Rows deleted, which must be zero.** Only the flag clears; the row and its data
  stay. A repair that deletes is a data-loss path.
- **First-run cost and steady-state cost.** The first is the one-time DDL plus the
  repair; every later call is the existence check.
- **The invariant holds after**: at most one covered row per group.
- **Uncovered rows still unlimited**, and a brand-new group's first covered row
  allowed.

## Then leave the read sites alone

With the constraint in place there is at most one active row per group, so a bare
`WHERE is_active = 1` is unambiguous. Adding `ORDER BY` to every read site is diff
churn that changes no behaviour, and it hides the fact that the ambiguity was fixed at
the source. Say in the plan why the reads were left untouched so a later reviewer does
not read the omission as an oversight.

## Verify on the versions that matter

Generated-column and partial-index behaviour differs between engines and between major
versions of one engine. A result on a local version is not evidence for the version
production runs. Probe the exact DDL there before trusting a green suite from another
version:

1. Create the table and the constraint.
2. Activate one row in a group.
3. Activate a second and require the unique violation.
4. Insert inactive rows in the same group and require success.
