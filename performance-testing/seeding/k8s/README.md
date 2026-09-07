# Kubernetes-based Parallel Seeding

This directory contains Kubernetes resources for running the farmer-registry seeding scripts in parallel across multiple pods to handle large data volumes efficiently.

## Architecture

The seeding system has been modified to support parallel execution across multiple Kubernetes pods:

- **Pod-specific ID ranges**: Each pod is assigned a unique range of functional IDs to prevent duplicates
- **Load balancing**: Farmers are distributed evenly across pods
- **Independent execution**: Each pod runs independently and writes directly to the database
- **Manifest merging**: After completion, individual pod manifests can be merged into a combined manifest

## Configuration

### Data Tiers and Pod Allocation

| Tier      | Total Farmers | Default Pods | Farmers per Pod |
|-----------|---------------|--------------|-----------------|
| smoke     | 10,000        | 1            | 10,000          |
| primary   | 10,000,000    | 10           | 1,000,000       |
| stretch   | 50,000,000    | 15           | 3,333,333       |
| stress    | 100,000,000   | 20           | 5,000,000       |

You can override the default pod count using the `--pods` parameter.

## Quick Start

### 1. Build and Push Docker Image

```bash
cd k8s
./build_and_push.sh
```

Or with custom image name/tag:

```bash
IMAGE_NAME=my-registry/farmer-seeding IMAGE_TAG=v1.0.0 ./build_and_push.sh
```

### 2. Generate Kubernetes Job Manifests

Generate job manifests for a specific tier:

```bash
python generate_jobs.py --tier primary --pods 10
```

This creates:
- Individual job files: `seeding-primary-pod-0.yaml` through `seeding-primary-pod-9.yaml`
- Kustomization file: `kustomization-primary.yaml`

### 3. Deploy Jobs

```bash
kubectl apply -k k8s/jobs/
```

Or specify the full path:

```bash
kubectl apply -k /home/techno-571/Desktop/openg2p/farmer-registry/performance-testing/seeding/k8s/jobs/
```

### 4. Monitor Progress

```bash
# Watch job status
kubectl get jobs -l app=farmer-registry-seeding -w

# Check pod logs
kubectl logs -l app=farmer-registry-seeding --tail=100 -f

# Check specific pod
kubectl logs seeding-primary-pod-0-xxxxx
```

### 5. Cleanup

```bash
kubectl delete -k k8s/jobs/
```

Or specify the full path:

```bash
kubectl delete -k /home/techno-571/Desktop/openg2p/farmer-registry/performance-testing/seeding/k8s/jobs/
```

## Advanced Usage

### Custom Configuration

Generate jobs with custom resource allocation:

```bash
python generate_jobs.py \
  --tier stress \
  --pods 20 \
  --image my-registry/farmer-seeding:v1.0 \
  --db-dsn "postgresql://user:pass@postgres-service:5432/g2p_registry" \
  --cpu-request "1000m" \
  --cpu-limit "4" \
  --memory-request "2Gi" \
  --memory-limit "8Gi"
```

### Merging Manifests

After parallel seeding completes, merge the individual pod manifests:

```bash
python merge_manifests.py --tier primary --pods 10
```

This creates a combined manifest file `seed_manifest_primary_combined.json`.

## Script Parameters

### generate_jobs.py

- `--tier`: Data volume tier (smoke, primary, stretch, stress)
- `--pods`: Number of pods (overrides tier default)
- `--output-dir`: Output directory for manifests (default: k8s/jobs)
- `--image`: Docker image name (default: openg2p/farmer-registry-seeding:latest)
- `--db-dsn`: Database connection string
- `--cpu-request/--cpu-limit`: CPU allocation per pod
- `--memory-request/--memory-limit`: Memory allocation per pod

### merge_manifests.py

- `--tier`: Data volume tier
- `--pods`: Number of pods that were used
- `--output-dir`: Directory containing manifest files (default: .)

## Running Locally with Pod Parameters

You can also test the pod-specific ID generation locally:

```bash
# Test pod 0 of 10
python run.py --tier primary --pod-index 0 --total-pods 10

# Test pod 1 of 10
python run.py --tier primary --pod-index 1 --total-pods 10
```

## ID Allocation Strategy

The system uses a pod-specific ID allocation strategy to prevent duplicates:

1. **Farmer IDs**: Each pod gets a range of `(total_farmers / total_pods) + 1000` IDs
2. **Household IDs**: Each pod gets a range of roughly 1/3 the Farmer ID range
3. **Other tables**: Use smaller, pod-specific ranges

The `+ 1000` buffer ensures no overlap even with uneven distribution.

## Database Requirements

- PostgreSQL database must be accessible from the Kubernetes cluster
- Schema and metadata must be pre-loaded (run the standard db-seed job first)
- Sufficient storage and I/O capacity for the target data volume
- Connection pool configured for concurrent writes

## Troubleshooting

### Jobs Fail to Start

Check pod logs for database connection issues:

```bash
kubectl logs -l app=farmer-registry-seeding --tail=50
```

### Duplicate IDs

If you suspect duplicate IDs, check:

1. All pods used different `--pod-index` values
2. The `--total-pods` parameter was consistent across all pods
3. The target farmer count was the same for all pods

### Uneven Distribution

For uneven distribution, the last pod gets any remainder farmers. This is intentional and handled automatically.

## Performance Considerations

- **Network**: Run pods close to the database (same cluster/region)
- **Resources**: Adjust CPU/memory based on data volume and cluster capacity
- **Batch Size**: The default batch size (75,000) is optimized for COPY operations
- **Indexes**: For large volumes, consider setting `DEFER_INDEXES=True` in config.py

## Example Workflow

Complete workflow for 10M farmer test:

```bash
# 1. Build image
cd k8s
./build_and_push.sh

# 2. Generate jobs for 10M farmers with 10 pods
python generate_jobs.py --tier primary --pods 10

# 3. Deploy
kubectl apply -k k8s/jobs/

# 4. Monitor (wait for completion)
kubectl get jobs -l app=farmer-registry-seeding -w

# 5. Copy manifests from pods (if needed)
kubectl cp seeding-primary-pod-0-xxxxx:/app/seed_manifest_pod0.json ./seed_manifest_pod0.json
# ... repeat for all pods

# 6. Merge manifests
python merge_manifests.py --tier primary --pods 10

# 7. Cleanup
kubectl delete -k k8s/jobs/
```