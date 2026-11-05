# Proving a quality target is reachable before exporting

A reviewer given an unreachable target produces plausible, confident, useless
advice. This is the gate that stops that brief being written, and the recipe for
the measurement behind it.

## The test

Ask: **is the target blocked by information loss that no downstream algorithm
can undo?** If yes, stop. If no, the brief is worth writing.

Three signals the answer is yes:

- A lossy stage (subsampling, quantisation, downscale, a hash, a bucket) sits
  upstream of the part you want to improve.
- The target is a fraction of an *abstract* space rather than of real observed
  data.
- Two different inputs are known to produce the same intermediate value.

## Enumerating the floor

Batch the whole space; do not sample. Sampling misses the collision structure,
which is exactly what decides the answer.

```python
BATCH = 1 << 22
seen = {}
for start in range(0, TOTAL, BATCH):
    idx = np.arange(start, min(start + BATCH, TOTAL), dtype=np.int64)
    out = lossy_stage(decode_inputs(idx))
    uniq, counts = np.unique(out, return_counts=True)
    for k, n in zip(uniq.tolist(), counts.tolist()):
        seen[k] = seen.get(k, 0) + n

distinct  = len(seen)
collided  = sum(n for n in seen.values() if n > 1)
worst_grp = max(seen.values())
```

`collided` is the hard floor: those inputs are identical before your code runs.
`worst_grp` says how badly — a group of 9 inputs collapsing to one value means
nine distinguishable things became one.

## Splitting the error by cause

For each input the current logic accepts, classify its loss:

| Cause | Meaning | Fixable by tuning? |
|---|---|---|
| Same-output | Its value was already shared with another input | No — gone before the gate |
| Boundary | It kept a unique value but landed outside the accepted set | Yes — the tunable part |

```python
share = [seen[c] for c in outputs[accepted_but_rejected]]
lost_shared   = sum(1 for s in share if s > 1)
lost_boundary = sum(1 for s in share if s == 1)
```

Report both. A gate losing 6,352 values of which 6,347 are same-output and 5 are
boundary has nothing left to tune, and that conclusion is invisible in the
headline retention figure.

## Cheap knobs, measured not assumed

Run each available setting through the same enumeration before recommending an
architectural change. Format range, bit depth, chroma mode, resampling filter —
one line each, same harness:

```
limited range   distinct 2,649,826   collided 99.92%   worst group 9
full range      distinct 4,006,243   collided 99.87%   worst group 5
```

A 0.05-point move on a 99.9% problem is a non-event. Saying so is a finding, and
it deletes a recommendation the reviewer would otherwise make.

## Re-aiming the metric

The abstract space is usually the wrong denominator. Logic scored over every
theoretical input caps near the floor; the same logic scored on real observed
inputs scores far higher, because reality occupies a small clustered slice.

When the floor blocks the abstract target, the replacement metric is:

- measured on real captured/observed data, not the full space;
- scored against labelled ground truth (true positives kept, false positives
  admitted), not against a theoretical region;
- stated with sample size and how the labels were produced.

That metric can be pushed toward the original target, and unlike the abstract
one it reflects what the user actually cares about.

## What to hand back instead of a brief

1. The floor, with the enumeration and its counts.
2. The split between already-gone and recoverable loss.
3. Which cheap knobs were tested and what each moved.
4. The re-aimed metric and the measurement plan that can succeed.
5. Explicitly: the original target is unreachable on this pipeline, and the
   number that proves it.

An outside reviewer is still useful after this, but the ask becomes "how do I
maximise this real-data metric" — a question with answers — instead of "how do I
reach 99.9% of a space that has already collapsed".
