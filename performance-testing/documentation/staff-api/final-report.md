# Final Report

Interpretation layer over [`raw-report.md`](raw-report.md) (every
measurement, verbatim, no interpretation) and, for the curated headline
endpoints, the `synthesize_templates/` CSVs under
[`../locust/api/templates/staff-api/`](../locust/api/templates/staff-api/)
once `scripts/synthesize_report.py` has run. See
[`test-scenarios.md`](test-scenarios.md) §3 for the Volume-Tier × Pod-Scale
matrix and the 3-Step + `db-sweep` model these map to.

**Pipeline:** raw Locust `--csv` output → `scripts/create_raw_report.py` →
[`raw-report.md`](raw-report.md) (all endpoints, no judgement) →
`scripts/synthesize_report.py` → curated `synthesize_templates/*.csv`
(headline endpoints + SLO + PASS/FAIL) → this document (interpretation,
cites both).

## The deliverables

| # | Output | Form | Source |
|---|--------|------|---|
| 1 | **Per-scenario capacity table** — endpoint, method, max sustainable RPS @ SLO, p50/p90/p95/p99/max, error %, saturating resource, per Volume-Tier/Pod-Scale cell | table | Step 1 (raw: [`raw-report.md`](raw-report.md); curated: `isolated-capacity.csv`) |
| 2 | **Per-pod resource profile** at max RPS (pod CPU, mem, DB conns) | table + graphs | Step 1 |
| 3 | **Latency-vs-RPS ("knee") and RPS-vs-users curves** | charts | Step 1 |
| 4 | **Blended capacity table**, per cell | table | Step 2 (raw: [`raw-report.md`](raw-report.md); curated: `blended-capacity.csv`) |
| 5 | **Horizontal scaling table + curve** — blended max RPS at Pod-Scale 1/2/3, same tier; efficiency; limiting factor | table + chart | *derived* — compare Step 2 across Pod-Scale |
| 6 | **Data-volume sensitivity** — capacity/latency vs Volume-Tier, same pod-scale | chart | *derived* — compare Step 1/2 across Volume-Tier |
| 7 | **Soak/endurance report** — RPS, p95, error rate, pod memory, DB conns over 8h; memory-trend verdict | time-series graphs | Step 3 (raw: [`raw-report.md`](raw-report.md); curated: `soak.csv`) |
| 8 | **DB capacity table** — threshold RPS + first bottleneck per tuning/volume/VM scenario; top slow queries | table | `db-sweep` (raw: [`raw-report.md`](raw-report.md); curated: `db-sweep.csv`) |
| 9 | **Bottleneck & tuning findings** — what saturated first; config changes that moved it (worker count, pool size, indexes, PgBouncer, max_connections, gp3 IOPS) | narrative | all |
| 10 | **Capacity / sizing model** — the headline business output (below) | formula/table | Synthesis |
| 11 | **Pass/fail vs SLO/NFR** | table | Synthesis |
| 12 | **Methodology + reproducible assets** — Locust scripts, env spec, versions, seed manifest | doc + repo | all |

Items **5, 7, 8, and 10** are what reviewers/funders care about most: the
scaling factor, proof of no time-decay, the DB ceiling, and the sizing
formula.

Async pipeline throughput (Celery) is **not** a current deliverable — see
[`test-scenarios.md`](test-scenarios.md) §1/§2.

## The capacity / sizing model (headline output)

Once primary-tier data exists, the sizing statement takes this form:

> *On the 3-node production profile (compute `m5a.4xlarge`, host-PG
> `t3a.2xlarge`), one `1 vCPU / 4 GB` staff-portal-api pod sustains **R** RPS of
> the blended workload (Step 2) at p95 ≤ SLO over the `primary` (10M farmer)
> Volume-Tier. At Pod-Scale 3 that becomes **R₃** RPS (efficiency **e**). The
> host PostgreSQL becomes the bottleneck at **D** RPS (`db-sweep`, tuned +
> PgBouncer), driven by `<bottleneck>`. Therefore, to serve a target of **T**
> RPS over **V** million records at the SLOs, provision **⌈T/R⌉** app pods
> (bounded by the DB ceiling D) and a DB of **`<size>`** with
> **`<max_connections>`** via PgBouncer.*

Not yet computable — requires primary-tier ramp-to-failure data (§4-§7
below).

## Report structure

Only a smoke-tier pipeline dry run exists so far (see the methodology note
in §2, and the `End-to-End › smoke › pod-1/2/3 › 1-isolated` sections of
[`raw-report.md`](raw-report.md)). It proved the raw-report/synthesize
pipeline works, surfaced one real methodology bug and one upstream bug
(§2), and — beyond the pipeline check — produced two real findings that
already stand independent of the primary-tier run: the AWE-hop bottleneck
(§4, §8) and a reported throughput improvement from the iam-core
JWKS/OIDC-metadata cache fix — though that fix does not appear in this
checkout's history (§8, item 3). It is not a capacity figure. Sections
5-7 and 9-11 are pending primary-tier ramp-to-failure data.

### 1. Executive summary
- **Reported improvement, code not found:** the iam-core JWKS/OIDC-metadata
  cache fix was reported to raise Pod-1 (2 vCPU / 2 GB) capacity from ~10
  to 30+ concurrent Locust users. The throughput change is real; the code
  responsible for it isn't in this checkout — see §8, item 3.
- **Headline:** Pod-Scale 1 (1 vCPU/4 GB) sustains **___ RPS** blended (Step 2) @ p95 ≤ SLO over Volume-Tier **`primary`**. _Not yet measured._
- **Scaling:** Pod-Scale 3 → **___ RPS** (efficiency **___**).
- **DB ceiling:** **___ RPS** (`db-sweep`, tuned + PgBouncer), limited by **______**.
- **Sizing model:** to serve **T RPS** over **V M** records → **___ app pods + DB `___`**.
- **Verdict vs SLO/NFR:** PASS / FAIL — _____.

### 2. Environment & methodology
- Chart version / image tags / git SHA: ______ (Prep step 1, not yet done).
- Nodes: compute `m5a.4xlarge` (16/64), storage host-PG `t3a.2xlarge` (8/32, T3-unlimited: __), RP `t3a.medium` — see [`environment-topology.md`](../environment-topology.md).
- Pod under test: 1 vCPU / 4 GB, `requests==limits`, HPA off, workers = __ (Prep step 6, not yet done — worker-count sweep pending).
- PostgreSQL 16: tuning = ______; PgBouncer = ______; max_connections = __.
- Volume-Tier(s) / Pod-Scale(s) tested: `smoke`/Pod-Scale 1-3 only so far (pipeline dry run). `primary` pending Prep completion.
- Load tool: Locust 2.46.3; run location: external host against the public perftest hostname (`STAFF_API_BASE`), i.e. **end-to-end** ingress, not in-cluster — Prep step 7 calls for an in-cluster Locust deployment for per-pod/scaling figures, still pending.
- **Methodology finding from the dry run:** the results-folder/template ingress label was initially wrong (`in-cluster` when the run actually went `end-to-end` through the public perftest hostname) — corrected; results are now segmented by ingress at the top level (`results/staff-api/<ingress>/...`) specifically so in-cluster and end-to-end runs of the same cell can never silently overwrite each other.
- **Known upstream bug, not a capacity finding:** in the `smoke` dry run, `register_read`'s `get_record_history` call failed 33/33 (`SYS-ERR-001`) — see [`seeding-design.md`](../seeding-design.md) (`change_request_source.value` on a plain `String` column). Needs a decision before real `primary`-tier Step 1 runs: exclude `get_record_history` from `register_read`'s pass/fail, or block on the upstream fix.

### 3. Pod configurations

| Service | Pod spec |
|---|---|
| farmer-registry (`staff-portal-api`) | 2 vCPU / 2 GB RAM |
| AWE | 2 vCPU / 2 GB RAM |
| Keycloak | 1 vCPU / 1 GB RAM |
| Master Data Service | to be configured |
| Audit Manager | to be configured |
| ID Generator | to be configured |

This is the topology the smoke-tier Pod-Scale 1/2/3 dry run (§4) actually
ran against — it's where the `2 vCPU / 2 GB` figure in §1's applied-fix
finding and §4's real-user table comes from. It does not match §2's
"1 vCPU / 4 GB" pod-under-test spec, which is `test-scenarios.md`'s
definition of the primary-tier measurement protocol and hasn't been
exercised yet — worth reconciling which spec the `primary`-tier run
actually uses before citing capacity numbers against it. AWE and Keycloak
are fixed-count pods on the shared compute node (§8) regardless of
`staff-portal-api`'s Pod-Scale — the specs above are the ceiling each
independently operates under while `staff-portal-api` scales 1→2→3.

### 4. Per-scenario capacity (Step 1)

Only the `smoke`-tier, Pod-Scale 1/2/3, `1-isolated` dry run exists so far.
Two effects are already visible in it.

Endpoints that stay inside registry-platform improve as pods scale, as
expected — less contention per pod:

| Endpoint | Pod-1 p95 | Pod-2 p95 | Pod-3 p95 |
|---|---|---|---|
| `get_change_request` | 860ms | 790ms | 620ms |
| `get_deduplication_register_results` | 780ms | 760ms | 600ms |

Endpoints that call out to AWE get worse as pods scale — the bottleneck is
the AWE hop, not registry-platform's own DB/CPU (root cause in §8):

| Endpoint | Pod-1 p95 | Pod-2 p95 | Pod-3 p95 |
|---|---|---|---|
| `list_tasks_for_request` | 920ms | 1100ms | 1100ms |
| `submit_task_decision` | 910ms | 980ms | 1000ms |

Full per-endpoint numbers: the `Step: 1-isolated` sections of
[`raw-report.md`](raw-report.md); curated headline-endpoint SLO/PASS-FAIL:
`synthesize_templates/isolated-capacity.csv` (after running
`scripts/synthesize_report.py --step isolated ...`). Latency-vs-RPS "knee"
charts (one per endpoint, across ramp steps) are pending — a single-step
dry run doesn't produce a ramp.

#### Real-life concurrent-user estimates (derived)

Locust's `wait_time` only paces between `@task` picks, not between the
individual API calls inside one task — a Locust "user" fires a whole
scenario's calls back-to-back, unlike a real case worker. Converting
Locust throughput into a real-user-equivalent figure uses Little's Law:

```
Real concurrent users = (unit completions/sec) × (real completion time, seconds)
```

**The unit is one fully-handled record, not one `@task` iteration.** An
earlier version of this table anchored on whichever endpoint fires once
per `@task` iteration (e.g. a session-summary widget, or a search-driven
loop that drains an unpredictable number of pending items per iteration).
That conflates "how many giant, variable-size batches finished" with "how
fast is one record actually processed," and for `cr_read_and_approve` and
`intake_read_and_approve` specifically it produced a false appearance of
throughput dropping at Pod-Scale 3. The corrected unit, per scenario, is
the realistic single-record journey a case worker actually performs —
search, land on one record, fire every API that record's detail view
needs, then (where applicable) act on it:

| Scenario | One unit of work | Anchor (fires once per unit) |
|---|---|---|
| register_read | search → zoom into 1 record → every tab, every pending CR on that tab, every version date on that tab | `get_subject_record` |
| cr_create | search → pick 1 record → its tabs/sections → edit 1 section → create the CR | `create_change_request` + `create_change_request_for_core_data` |
| cr_read_and_approve | search → pick 1 CR → its documents/schema/dedup/tasks → approve | `submit_task_decision` |
| intake_create | render the form → save every section → fetch → finalize | `finalize_intake_form_submission` |
| intake_read_and_approve | search → pick 1 submission → its documents/dedup/tasks → approve | `submit_task_decision` |

For each API in a unit's chain, its contribution to "total time for 1
unit" is **its own average response time × how many times it actually
fires per unit** (`endpoint's Request Count ÷ anchor's Request Count`,
both from the same pod's CSV) — not counted once each, since several of
these calls are structurally repeated per record (a record has several
tabs; a tab has however many pending items it has) or repeated by the
test's own search/candidate-discovery process. `T_real` (assumed real
completion time — unchanged from before) is then multiplied by the
anchor's own RPS, not a session/summary endpoint's.

**register_read** — 1 register record fully read:

| API | Pod-1 avg ms (×/unit) | Pod-2 avg ms (×/unit) | Pod-3 avg ms (×/unit) |
|---|---|---|---|
| `search_in_a_register` | 370ms (×1.00) | 374ms (×1.00) | 339ms (×1.00) |
| `get_subject_record` | 244ms (×1.00) | 241ms (×1.00) | 208ms (×1.00) |
| `get_all_tabs` | 263ms (×1.00) | 256ms (×1.00) | 214ms (×1.00) |
| `get_tab_sections` | 270ms (×6.73) | 266ms (×6.81) | 224ms (×6.84) |
| `get_tab_records` | 320ms (×6.72) | 312ms (×6.80) | 262ms (×6.83) |
| `get_number_of_pending_change_requests` | 244ms (×6.70) | 240ms (×6.80) | 201ms (×6.82) |
| `get_change_requests` | 268ms (×6.69) | 266ms (×6.79) | 222ms (×6.82) |
| `get_change_request_documents` | 220ms (×1.87) | 237ms (×2.49) | 201ms (×1.96) |
| `get_section_ui_schema` | 223ms (×1.86) | 235ms (×2.49) | 201ms (×1.96) |
| `get_change_request` | 266ms (×1.86) | 288ms (×2.48) | 250ms (×1.95) |
| `list_tasks_for_request` | 268ms (×1.86) | 307ms (×2.48) | 291ms (×1.95) |
| `get_deduplication_change_request_results` | 224ms (×1.86) | 241ms (×2.48) | 207ms (×1.95) |
| `get_deduplication_register_results` | 234ms (×1.86) | 234ms (×2.48) | 205ms (×1.95) |
| `get_number_of_versions` | 262ms (×6.68) | 259ms (×6.77) | 214ms (×6.80) |
| `get_version_dates` | 258ms (×6.68) | 250ms (×6.77) | 209ms (×6.80) |
| `get_versions_for_a_date` | 263ms (×3.99) | 270ms (×4.22) | 220ms (×4.36) |
| **Total time for 1 register record** | **15.45s** | **16.66s** | **13.45s** |

| | Pod-1 | Pod-2 | Pod-3 |
|---|---|---|---|
| Anchor RPS (`get_subject_record`) | 1.007 | 1.494 | 2.088 |
| T_real | 30s | 30s | 30s |
| Real concurrent users | 30 | 45 | 63 |

**cr_create** — 1 change request effected:

| API | Pod-1 avg ms (×/unit) | Pod-2 avg ms (×/unit) | Pod-3 avg ms (×/unit) |
|---|---|---|---|
| `search_in_a_register` | 382ms (×0.36) | 336ms (×0.35) | 296ms (×0.36) |
| `get_subject_record` | 291ms (×0.18) | 226ms (×0.18) | 178ms (×0.18) |
| `get_all_sections` | 602ms (×0.18) | 516ms (×0.18) | 422ms (×0.18) |
| `get_all_tabs` | 285ms (×0.18) | 246ms (×0.18) | 185ms (×0.18) |
| `get_tab_sections` | 298ms (×1.25) | 248ms (×1.26) | 196ms (×1.28) |
| `get_tab_records` | 354ms (×1.25) | 294ms (×1.25) | 232ms (×1.27) |
| `get_attribute_values` | 273ms (×0.05) | 245ms (×0.05) | 195ms (×0.04) |
| `create_change_request` | 564ms (93% of CRs) | 509ms (94% of CRs) | 518ms (94% of CRs) |
| `create_change_request_for_core_data` | 584ms (7% of CRs) | 566ms (6% of CRs) | 543ms (6% of CRs) |
| **Total time for 1 change request effected** | **1.75s** | **1.50s** | **1.32s** |

Two different things are happening in this table, and they look similar
but aren't. `search_in_a_register`/`get_subject_record`/`get_all_sections`/
`get_all_tabs` carry ratios below 1.0 because one of these calls is
genuinely **shared** across several CRs from the same search/record visit
— `create_change_requests` fires them once per outer iteration, then
creates one CR per tab that has a configured section (a few CRs per
visit), so each call's cost is amortized, not skipped. `create_change_request`
and `create_change_request_for_core_data` are different: every single CR
creation calls **exactly one** of the two (core-section CRs route to the
`_for_core_data` endpoint, non-core to the other — mutually exclusive,
never both, never neither), which is why their two shares sum to exactly
100% at every pod. There's no sharing or skipping here — the percentages
say what fraction of CRs go through each variant, and the "total time for
1 CR" row already reflects the correct probability-weighted blend of the
two variants' costs (e.g. pod-1: 0.93×564ms + 0.07×584ms ≈ 565ms for
"the call that actually creates the CR," whichever variant it turns out
to be).

| | Pod-1 | Pod-2 | Pod-3 |
|---|---|---|---|
| Anchor RPS (`create_change_request` + `create_change_request_for_core_data`) | 7.272 | 11.823 | 13.127 |
| T_real | 30s | 30s | 30s |
| Real concurrent users | 218 | 355 | 394 |

**cr_read_and_approve** — 1 change request approved:

| API | Pod-1 avg ms (×/unit) | Pod-2 avg ms (×/unit) | Pod-3 avg ms (×/unit) |
|---|---|---|---|
| `search_in_change_request` | 374ms (×2.17) | 415ms (×1.01) | 314ms (×1.17) |
| `get_change_request_documents` | 306ms (×5.09) | 295ms (×3.07) | 166ms (×3.03) |
| `get_section_ui_schema` | 306ms (×5.09) | 296ms (×3.07) | 164ms (×3.03) |
| `get_change_request` | 374ms (×5.07) | 360ms (×3.06) | 205ms (×3.03) |
| `get_deduplication_change_request_results` | 312ms (×5.06) | 302ms (×3.06) | 168ms (×3.03) |
| `get_deduplication_register_results` | 312ms (×5.06) | 299ms (×3.06) | 167ms (×3.02) |
| `list_tasks_for_request` | 364ms (×5.05) | 370ms (×3.05) | 294ms (×3.02) |
| `submit_task_decision` | 480ms (×1.00) | 453ms (×1.00) | 377ms (×1.00) |
| **Total time for 1 change request approved** | **11.30s** | **6.76s** | **4.27s** |

The ×2-5 ratios on the detail/dedup/list_tasks calls reflect the
locustfile's own design — one claimed search term is drained of every
currently-pending CR before release, and most of those CRs get looked at
(documents, dedup, `list_tasks_for_request`) without reaching an
actionable task, so only a fraction end in `submit_task_decision`. That
ratio (and hence the "total time for 1 CR") itself drops sharply from
Pod-1 to Pod-3 in this run — worth treating as a property of this
specific test's timing/data availability, not a stable per-CR constant.

| | Pod-1 | Pod-2 | Pod-3 |
|---|---|---|---|
| Anchor RPS (`submit_task_decision`) | 1.437 | 3.939 | 4.367 |
| T_real | 30s | 30s | 30s |
| Real concurrent users | 43 | 118 | 131 |

**intake_create** — 1 intake submission created:

| API | Pod-1 avg ms (×/unit) | Pod-2 avg ms (×/unit) | Pod-3 avg ms (×/unit) |
|---|---|---|---|
| `render_intake_form` | 257ms (×1.03) | 205ms (×1.02) | 162ms (×1.02) |
| `save_intake_form_submission` | 530ms (×9.17) | 407ms (×9.12) | 304ms (×9.13) |
| `get_intake_form_submission` | 383ms (×1.01) | 298ms (×1.00) | 225ms (×1.00) |
| `finalize_intake_form_submission` | 734ms (×1.00) | 613ms (×1.00) | 510ms (×1.00) |
| **Total time for 1 intake submission created** | **6.24s** | **4.84s** | **3.67s** |

`save_intake_form_submission` fires ~9.1 times per submission (one call
per form section — a stable ratio across all three pods, unlike the
read-and-approve scenarios above), so it dominates the total.

| | Pod-1 | Pod-2 | Pod-3 |
|---|---|---|---|
| Anchor RPS (`finalize_intake_form_submission`) | 1.612 | 2.734 | 3.390 |
| T_real | 60s | 60s | 60s |
| Real concurrent users | 97 | 164 | 203 |

**intake_read_and_approve** — 1 intake submission approved:

| API | Pod-1 avg ms (×/unit) | Pod-2 avg ms (×/unit) | Pod-3 avg ms (×/unit) |
|---|---|---|---|
| `search_in_intake_form_submissions` | 547ms (×16.71) | 556ms (×8.84) | 332ms (×1.61) |
| `get_intake_form_submission` | 160ms (×1.05) | 213ms (×1.08) | 233ms (×1.22) |
| `get_intake_form_documents` | 107ms (×1.05) | 145ms (×1.08) | 161ms (×1.22) |
| `get_deduplication_intake_form_register_results` | 114ms (×1.05) | 151ms (×1.08) | 162ms (×1.22) |
| `get_deduplication_intake_form_intake_form_results` | 114ms (×1.05) | 147ms (×1.08) | 161ms (×1.22) |
| `list_tasks_for_request` | 175ms (×1.05) | 226ms (×1.08) | 294ms (×1.22) |
| `submit_task_decision` | 217ms (×1.00) | 280ms (×1.00) | 342ms (×1.00) |
| **Total time for 1 intake submission approved** | **10.07s** | **6.14s** | **2.11s** |

The search ratio here (×16.7 → ×8.8 → ×1.6) is the biggest swing in any of
these five tables. ~20% of iterations deliberately search a miss-token
(no pending results, no approval — see the locustfile's intentional-miss
design) and the rest page through every unclaimed search term until one
has pending work, so this number reflects how much of the seeded backlog
was still findable per term at the time each pod's run happened, not a
fixed per-submission search cost. Treat this scenario's "total time for 1
submission" figure as the least stable of the five.

| | Pod-1 | Pod-2 | Pod-3 |
|---|---|---|---|
| Anchor RPS (`submit_task_decision`) | 1.130 | 3.012 | 7.733 |
| T_real | 30s | 30s | 30s |
| Real concurrent users | 34 | 90 | 232 |

**All five scenarios now scale up with Pod-Scale** under this corrected,
per-record anchor — including `cr_read_and_approve` and
`intake_read_and_approve`, which the session/summary-anchored version of
this table had shown shrinking at Pod-Scale 3. That earlier drop was an
artifact of the anchor, not a real capacity regression: once throughput is
measured as "records/CRs/submissions actually completed per second"
instead of "outer search-and-drain sessions completed per second," both
scenarios scale cleanly.

This does **not** contradict the separate peak-concurrency-ceiling finding
from this conversation's cr_read_and_approve re-analysis (the ramp shape
still freezes at a lower user count at Pod-Scale 3 than Pod-Scale 2, and
AWE still logs connection-reset errors under load) — that is a tail/ceiling
effect visible in the ramp shape's own ramp-to-breach behavior, not in
this typical-case, whole-run throughput number. The two findings answer
different questions: this table says "the typical CR/submission is handled
faster and more of them get done per second as pods scale"; the
peak-concurrency finding says "the *ceiling* before things start failing
is still capped by AWE's fixed capacity." Both are true at once.

These are still `1-isolated` runs, each scenario measured with the pod
running only that workload — each figure is that scenario's ceiling in
isolation, not additive. A pod serving the real mixed workload contends
for the same DB connections, CPU, and AWE capacity across all five
scenarios at once, so the real mixed-workload concurrent-user number is
lower than each isolated figure.

#### Step-by-step: theoretical capacity (server time only, before think-time)

The tables above give "real concurrent users" from the *measured* RPS
(Locust's own completions ÷ elapsed time, think-time and all). This is a
second, independent derivation of the same quantity, built the other
direction — starting from pure server-side cost and this run's actual
concurrency, then substituting a realistic human pace for the test's own
think-time:

```
records/sec (1 user, zero pauses)   = 1 ÷ (seconds per record, from the per-API tables above)
total records/sec (server capacity) = N (peak concurrent users this run reached) × records/sec (1 user)
realistic users                     = total records/sec × T_real
```

`N` is each scenario's peak `User Count` from its own `_stats_history.csv`
— the highest concurrency the ramp shape reached before freezing at its
SLO breach, i.e. the actual number of simulated users generating load
when this pod's numbers above were recorded.

| Scenario | Pod | Seconds/record | Records/sec (1 user) | N (peak users) | Total records/sec | T_real | Realistic users |
|---|---|---|---|---|---|---|---|
| register_read | Pod-1 | 15.45s | 0.0647 | 28 | 1.812 | 30s | **54** |
| register_read | Pod-2 | 16.66s | 0.0600 | 48 | 2.880 | 30s | **86** |
| register_read | Pod-3 | 13.45s | 0.0744 | 56 | 4.164 | 30s | **125** |
| cr_create | Pod-1 | 1.75s | 0.5725 | 24 | 13.741 | 30s | **412** |
| cr_create | Pod-2 | 1.50s | 0.6652 | 36 | 23.948 | 30s | **718** |
| cr_create | Pod-3 | 1.32s | 0.7548 | 36 | 27.171 | 30s | **815** |
| cr_read_and_approve | Pod-1 | 11.30s | 0.0885 | 28 | 2.478 | 30s | **74** |
| cr_read_and_approve | Pod-2 | 6.76s | 0.1480 | 48 | 7.104 | 30s | **213** |
| cr_read_and_approve | Pod-3 | 4.27s | 0.2342 | 32 | 7.495 | 30s | **225** |
| intake_create | Pod-1 | 6.24s | 0.1602 | 20 | 3.204 | 60s | **192** |
| intake_create | Pod-2 | 4.84s | 0.2068 | 28 | 5.790 | 60s | **347** |
| intake_create | Pod-3 | 3.67s | 0.2722 | 28 | 7.623 | 60s | **457** |
| intake_read_and_approve | Pod-1 | 10.07s | 0.0993 | 24 | 2.384 | 30s | **72** |
| intake_read_and_approve | Pod-2 | 6.14s | 0.1627 | 40 | 6.509 | 30s | **195** |
| intake_read_and_approve | Pod-3 | 2.11s | 0.4746 | 32 | 15.187 | 30s | **456** |

**Why these numbers are higher than the measured-RPS table above them,
scenario by scenario:**

- `register_read`'s gap (54/86/125 here vs. 30/45/63 measured-RPS) is
  fully explained: this method strips out the locustfile's own 1-3s
  inter-tab sleep and 0.5-2s base `wait_time`, which together account for
  essentially all of the difference (worked through in this
  conversation — the two reconcile to within ~3-15% at every pod).
- The other four scenarios have no per-tab sleep, only Locust's 0.5-2s
  base `wait_time` between `@task` iterations — a small, arbitrary
  pacing choice for the test, not a stand-in for real think-time. Their
  gap (roughly 1.7-2x higher here than the measured-RPS table) is that
  same effect at a smaller scale: this method replaces that ~0.5-2s
  artificial pause with the realistic `T_real` (30s/60s) instead of
  leaving it mixed into the measured rate.

**These numbers are not a replacement for the measured-RPS table — they
answer a different question and depend on an assumption the measured
table doesn't need.** The measured-RPS table needs no assumption about
`N`; it reads directly off what Locust actually observed. This table
needs `N` (peak concurrent users) as an input, and its result is only as
good as that number — `N` is a single peak sample from a 1-second-resolution
history file, not a controlled, sustained concurrency level. Treat this
table as a cross-check that confirms the same scaling pattern from a
different angle (server-time-only capacity, independent of the test's own
pacing), not as a more-precise replacement for the directly measured
figures above. **Once the locustfiles are changed to remove artificial
pauses and re-run, the measured-RPS table and this table should converge**
— at that point, re-derive "real concurrent users" directly from the new
measured RPS × `T_real`, the same way the measured-RPS table already
does, rather than re-doing this N/T reconstruction.

### 5. Blended capacity, scaling, and data-volume sensitivity (Step 2)

Pending — no Step 2 (blended) run exists yet; only Step 1 (isolated, §4)
has run, on the smoke tier. Once a blended run exists: derive the scaling
curve (Pod-Scale 1→2→3, fixed tier) and the volume-sensitivity chart
(Volume-Tier swept, fixed pod-scale) from [`raw-report.md`](raw-report.md)'s
`Step: 2-blended` sections and `synthesize_templates/blended-capacity.csv`
— see [`test-scenarios.md`](test-scenarios.md) §3. §4's isolated data
already points to AWE as the likely limiting factor for the blended
workload's approval-submission share.

### 6. Endurance / soak (Step 3)
Pending — no soak run exists yet. Planned: 8h at 80% of this cell's Step 2
max RPS, once that figure exists, reading RPS/p95/error-rate/pod-memory/DB-conns
time series from [`raw-report.md`](raw-report.md)'s `Step: 3-soak` sections
(Locust's `_stats_history.csv`).

### 7. Database ceiling (`db-sweep`)
Pending — no `db-sweep` run exists yet. Planned source:
[`raw-report.md`](raw-report.md)'s `Step: 4-db-sweep` sections
(hand-recorded readings), a latency-vs-volume chart, and the top
`pg_stat_statements`.

### 8. Bottlenecks & tuning

Nine changes were reported as identified/applied against this list; each
is checked here against the actual commit history in the `registry-platform`,
`awe`, `iam`, and `openg2p-fastapi-common` repos (this `venky-github`
checkout, which is ahead of `openg2p-github` on all four) rather than taken
at face value.

**1. AWE worker/pool tuning — applied, but not literally Gunicorn.**
`awe` commit `072e943` ("Increase UVICORN workers...") raised
`UVICORN_WORKERS` 1→2 in the `Dockerfile`. `docker-entrypoint.sh` still
runs `exec uvicorn awe.main:app --workers "${UVICORN_WORKERS}"` directly —
there is no `gunicorn` dependency or invocation anywhere in the `awe` repo,
so this is uvicorn's own multi-worker flag, not a Gunicorn-managed
uvicorn-worker setup. The same commit also changed `db.py`'s *default*
pool_size/max_overflow (used only when the env vars are unset) from 20/15
back to 10/5 — but the deployed values come from
`helm/openg2p-awe/values.yaml`, which an earlier same-day commit
(`155463b`) set to `DB_POOL_SIZE=5`/`DB_POOL_MAX_OVERFLOW=10`. Net effect
in production: total connection ceiling is unchanged at 15, just
re-split (smaller persistent pool, larger overflow) and now
environment-configurable instead of hardcoded (see item 8).

**2. Composite index in registry-platform — applied.**
`ix_change_requests_lookup` on
`g2p_register_change_requests(register_id, internal_record_id, tab_id, created_at)`,
added in `59209d7` (G2P-5507, backing `get_change_requests_flattened`) and
extended with `approval_status` in `5c0a396` (G2P-5510, backing
`get_number_of_pending_change_requests`). A separate, non-composite index
was also added on `g2p_registers.last_approved_at` in `c8efcac` (G2P-5513,
`search_in_a_register`). None of this touches the `get_register_summary_data`
count path — see item 5.

**3. iam-core oidc_client/jwks ContextVar fix — not found in the repo.**
Checked `iam_core/context.py`, `oidc_client.py`, and `jwks_helper.py` at
current HEAD across all local branches, with no uncommitted or stashed
changes: `jwks_cache` and `server_metadata_cache` are still plain
`ContextVar`s, unchanged since the original `G2P-5128` consolidation
commit — the same ContextVar-copy-per-asyncio-Task bug flagged earlier in
this conversation. `fastapi_cache`
is in active use elsewhere in `iam-core` (role-permission caching,
`fe6d788`) and in `iam-staff-portal-api`, but not wired into these two
files. Either this change hasn't been pushed to this checkout yet, or it
landed in a different repo/branch — worth confirming before treating the
~1000ms `get_subject_record` cost as fixed.

**4. Connection pooling via singleton session-maker — applied.**
`openg2p-fastapi-common` commit `17057b7` (G2P-5620) replaced the
per-call `async_sessionmaker(dbengine.get())` construction with
`get_async_session_maker()`, backed by `GlobalVar` (a plain instance
attribute, not a `ContextVar` — genuinely process-wide) and memoized after
first build. Pool size/overflow are now `Settings` fields
(`db_pool_size`/`db_pool_max_overflow`, defaults 5/10). `registry-platform`
adopted it the same day (`41147a9`, G2P-5620) across its services.

**5. Registry-platform caching changes, Aug 12 – Sep 2 (this checkout) —
applied, mixed effect.** In commit order:
  - `59209d7`/`5c0a396`/`c8efcac`/`4342369`/`7ade042`/`3fa183e` (G2P-5507–5513,
    Aug 12): per-endpoint tuning for `get_change_requests_flattened`,
    `get_number_of_pending_change_requests`, `get_subject_record`,
    `get_all_tabs`, `get_version_dates`, `get_versions_for_a_date`,
    `search_in_a_register` — mostly the indexes in item 2 plus new cached
    helpers `_get_register_definition`/`_require_register_definition` and
    `_get_tab_sections` (`single_id_key_builder`/`pair_id_key_builder`),
    reused across several of these methods instead of re-querying inline.
  - `b852f24` (G2P-5514): wrapped `get_register_summary_data` itself in
    `@cache(key_builder=data_policies_key_builder)` (TTL fixed at 60s in
    `0699d12`), and moved tab→sections assembly in
    `g2p_register_metadata_service` behind a similar cache, replacing an
    N-per-section validation loop with one join query. **This masks but
    does not fix** the underlying per-register N+1 unindexed `COUNT(*)` —
    see item 5's continuation below and the original finding in this
    conversation: the 60s cache absorbs repeat calls, but a cold cache or
    TTL expiry under load still pays the full sequential-scan cost, and
    concurrent misses aren't coalesced (a stampede risk `fastapi-cache`'s
    `@cache` doesn't address). The proposed
    `pg_stat_user_tables.n_live_tup` approximate-count fix was not applied.
  - `0699d12` (G2P-5609): namespaced, invalidated `@cache` on AWE-policy
    resolution (`policy_lookup_key_builder`, explicit
    `FastAPICache.clear(namespace=...)` on create/update/delete) — correctly
    designed and covered by unit tests (cache-hit, cache-miss-on-different-key,
    invalidation-on-write).
  - `37284e2`: the same thin-cached-wrapper-plus-`_assemble_*` pattern
    extended to intake-form services (`render_intake_form`, `get_all_tabs`,
    `get_all_sections`).
  - `2ef461b`: validation-method refactors in the same services, no new
    caching primitives.

**6. Async AWE-request creation for `create_cr`/`finalize_intake` — pending,
confirmed.** Both still call AWE synchronously to create the workflow. A
Celery worker/beat setup already exists in this codebase
(`celery/openg2p-registry-celery-beat`) for the data-ingest pipeline, but
nothing yet routes AWE request creation through a queue table or a
Celery task.

**7. Second AWE call in `list_tasks_for_request` — not found in the repo.**
`awe_helper.py`'s `list_tasks_for_request` still makes two sequential
`_list_tasks` calls (`assignee="*"` then `assignee="me"`) — unchanged
since it was introduced (`0ac9dce`), across all branches, no uncommitted
diff. Same caveat as item 3: this is still the contributor behind §4's
`list_tasks_for_request` p95 growth and needs confirming before it's
cited as resolved.

**8. AWE connection-pool parameters made configurable — applied.**
`DB_POOL_SIZE`/`DB_POOL_MAX_OVERFLOW`/`DB_POOL_RECYCLE` env vars, added in
`155463b` and adjusted in `072e943` (both `awe`) — see item 1 for the
actual deployed numbers.

**Also confirmed while auditing the above (not in the original list):**
`155463b` added several more indexes on AWE's own tables
(`ApprovalTask`, `ApprovalRequest`, `ApprovalDecision`, `ApprovalEvent`,
`UserDelegation`), switched `list_tasks`/`decide` from `selectinload` to
`joinedload` to fold a decision's owning-request lookup into one query
instead of a second `session.get()`, reduced `search_requests`'s max
`limit` from 500 to 100, and added a 5-minute in-process TTL cache for
`_load_policy` (`engine.py`). `resolver.py`'s dead `_ResolutionCache` and
`auth_id_type_config_cache`'s `ContextVar` bug (both flagged earlier in
this conversation) remain unaddressed — real gaps for `role`/`group`
approver rules and for the sibling `auth_models` package respectively, but
a no-op on the current `rule_type='user'` seed data.

### 9. Pass / fail vs SLO/NFR
Pending overall PASS/FAIL — no primary-tier SLO run exists yet. The one
completed check, the smoke-tier pipeline dry run, surfaced a failing
endpoint that is a known upstream bug rather than a capacity finding:
`register_read`'s `get_record_history` failed 33/33 (`SYS-ERR-001`, §2).

### 10. Recommendations & sizing guide
- **Production sizing:** not yet computable — requires primary-tier
  blended-capacity data (§5).
- **Config recommendations:** confirm items 3 and 7 from §8 actually
  landed (they don't appear in this checkout's history) before treating
  them as done; the remaining open items from §8 — moving AWE-request
  creation onto Celery (item 6), and the `get_register_summary_data`
  approximate-count fix (item 5) — are still open.
- **Follow-ups / known limits:** async-pipeline throughput for the
  AWE-request-creation queue (item 6 above) is separate from the existing
  ingest-pipeline Celery deployment and not covered by this round's
  scenarios ([`test-scenarios.md`](test-scenarios.md) §1/§2);
  `register_read`'s `get_record_history` upstream bug (§2) needs
  resolution before primary-tier runs; §3's pod-spec mismatch needs
  reconciling before primary-tier numbers are cited.

### 11. Appendix
- Raw Locust CSVs, Grafana dashboard exports, `pg_stat_statements` dumps.
- Locust config + seed manifest + exact postgresql.conf diffs.

## Conventions

- Always report **p95 and p99** (not p95 alone) and **error rate by type**.
- Every number carries its **pinned config** (Pod-Scale, worker count,
  Volume-Tier, DB tuning) — a bare "RPS" is meaningless without it.
- Report **median of ≥2 runs** plus spread; flag any run-to-run variance
  > ~10%.
- State the **ingress point** (in-cluster vs end-to-end) for every figure.
