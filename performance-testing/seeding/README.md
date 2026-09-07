# Bulk seed generator — quick start

Generates realistic, high-volume `Farmer` register data (households, farmers,
household members, lands, crops, livestock, farm inputs, membership details,
and `*_history` twins) directly into PostgreSQL via `COPY`, for the Volume-
Tiers defined in
[`../documentation/seeding-design.md`](../documentation/seeding-design.md).
See that document for the design rationale (generation DAG, why fields are
generator-computed instead of ORM-computed, search-anchor design, known
simplifications and the one known upstream issue) — this file is just
install/run.

## Prerequisites

1. **Configuration/meta-data must already be loaded** — register definitions,
   schemas, UI tabs/sections, attribute lookups. This is the platform's
   `db-seed` Job (`dbSeed.enabled=true`, **not** `dbSeed.loadSampleData=true`
   — that's a handful of demo rows, not a volume tier). The generator reads
   real `g2p_register_definitions` / `g2p_register_sections` /
   `g2p_register_ui_tab_sections` rows at runtime and will fail loudly if
   they're missing.
2. **Run close to the DB** — COPY over a slow network link will bottleneck
   before Postgres does.
3. `pip install -r requirements.txt` (`psycopg2-binary`, `Faker`).

## Running

### Local Single-Pod Execution

```sh
cd performance-testing/seeding
export SEED_DB_DSN=postgresql://user:pass@host:5432/g2p_registry
python run.py --tier smoke      # 10K farmers, sanity check first
python run.py --tier primary    # 10M farmers, the headline benchmark figure
```

### Kubernetes Parallel Execution

For large data volumes (10M+), use Kubernetes Jobs for parallel execution:

```sh
cd performance-testing/seeding/k8s

# Build and push Docker image
./build_and_push.sh

# Generate job manifests (10M farmers with 10 parallel pods)
python generate_jobs.py --tier primary --pods 10

# Deploy all jobs
kubectl apply -k k8s/jobs/kustomization-primary.yaml

# Monitor progress
kubectl get jobs -l app=farmer-registry-seeding -w
kubectl logs -l app=farmer-registry-seeding --tail=100 -f

# Merge manifests after completion
python merge_manifests.py --tier primary --pods 10
```

See [`k8s/README.md`](k8s/README.md) for detailed Kubernetes setup and configuration.

### Local Testing with Pod Parameters

Test pod-specific ID allocation locally:

```sh
python run.py --tier primary --pod-index 0 --total-pods 10
python run.py --tier primary --pod-index 1 --total-pods 10
```

## Tiers

| Tier    | Farmers | Default Pods | Use Case              |
|---------|---------|--------------|-----------------------|
| smoke   | 10K     | 1            | Quick sanity check    |
| primary | 10M     | 10           | Main benchmark        |
| stretch | 50M     | 15           | Scaling test          |
| stress  | 100M    | 20           | Maximum load test     |

See `config.DATA_VOLUME_TIERS` for definitions. For a `smoke`-tier correctness check, also set
`config.DEFER_INDEXES = False` first — see
[`seeding-design.md`](../documentation/seeding-design.md) "Load mechanics" for
why.

## Verify after seeding

```sql
-- row counts
SELECT relname, n_live_tup FROM pg_stat_user_tables
 WHERE relname LIKE 'g2p_register_%' ORDER BY n_live_tup DESC;

-- pg_trgm present
SELECT extname FROM pg_extension WHERE extname='pg_trgm';
\di+ *register*

-- a representative anchor search uses an index (not a seq scan)
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM g2p_register_farmers WHERE search_text ILIKE '%<an anchor>%' LIMIT 20;
```

Then warm the cache (representative reads) before measuring.
