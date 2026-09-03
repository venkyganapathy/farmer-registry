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
Real concurrent users = (scenario completions/sec) × (real completion time, seconds)
```

Completions/sec is read from the one endpoint each scenario calls exactly
once per completed `@task` iteration (verified against each locustfile),
not the "Aggregated" row, which sums every endpoint call at its own
per-iteration frequency and is not a completions/sec figure:

| Scenario | Anchor endpoint |
|---|---|
| register_read | `get_subject_record` |
| cr_create | `get_all_tabs` |
| cr_read_and_approve | `get_register_change_request_summary_data` |
| intake_create | `finalize_intake_form_submission` |
| intake_read_and_approve | `get_intake_form_submissions_summary` |

Real completion times per scenario (assumed): register-read 30s, cr-create
30s, cr-read-and-approve 30s, intake-create 60s, intake-read-and-approve
30s.

| Scenario | T_real | Pod-1 RPS → users | Pod-2 RPS → users | Pod-3 RPS → users |
|---|---|---|---|---|
| register_read | 30s | 1.007 → 30 | 1.494 → 45 | 2.088 → 63 |
| cr_create | 30s | 1.324 → 40 | 2.145 → 64 | 2.423 → 73 |
| cr_read_and_approve | 30s | 0.482 → 14 | 0.481 → 14 | 0.280 → 8 |
| intake_create | 60s | 1.612 → 97 | 2.734 → 164 | 3.390 → 203 |
| intake_read_and_approve | 30s | 2.148 → 64 | 3.114 → 93 | 1.793 → 54 |

`register_read`, `cr_create`, and `intake_create` scale with pod count, as
expected. `cr_read_and_approve` and `intake_read_and_approve` don't:
`cr_read_and_approve` is flat Pod-1→Pod-2 and drops at Pod-3 (14→14→8);
`intake_read_and_approve` rises then drops at Pod-3 (64→93→54). Both are
the AWE-touching, decision-submitting scenarios — this is the AWE/Keycloak
bottleneck (§8) showing up as a real-user-capacity regression, not just a
latency-percentile effect: scaling `staff-portal-api` pods buys more
`register_read`/`cr_create`/`intake_create` capacity but actively hurts the
two approval-workflow scenarios past Pod-Scale 2.

These are `1-isolated` runs, each scenario measured with the pod running
only that workload — each figure is that scenario's ceiling in isolation,
not additive. A pod serving the real mixed workload contends for the same
DB connections, CPU, and AWE/Keycloak capacity across all five scenarios
at once, so the real mixed-workload concurrent-user number is lower than
each isolated figure, particularly once
`cr_read_and_approve`/`intake_read_and_approve` traffic starts contending
with the others for AWE.

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
