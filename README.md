# RDA PostgreSQL Management

This repository contains:

- Python package to manage RDA PostgreSQL databases
- Helm charts for PostgreSQL clusters via CloudNativePG

## PostgreSQL Clusters

### Architecture
- **pgdb01** (NWSC cluster): Primary database
- **pgdb02** (ML cluster): Replication target (streaming replica from pgdb01)
- **pgdb03** (ML cluster)

All Postgres clusters are managed via the [CloudNativePG operator](https://cloudnative-pg.io/) using Helm charts from `https://cloudnative-pg.github.io/charts`.

### Deployment
All PostgreSQL resources are automatically deployed and updated via **ArgoCD**. To make changes:

1. Update the relevant YAML files in this repository
2. Commit and push changes
3. ArgoCD will automatically apply the updates to the clusters

No manual `kubectl apply` or Helm commands are needed for routine updates.

### Rebuilding Replication (pgdb02)

If replication fails or pgdb02 becomes out of sync with pgdb01, you can rebuild it by deleting the cluster resource. The cluster will automatically re-bootstrap from pgdb01 via `pg_basebackup`.

**Note:** Make sure you are targeting the right database before running any of these commands.

**Option 1: Via ArgoCD UI**
1. Navigate to the pgdb02 application in [ArgoCD](https://mlc1-argo.k8s.ucar.edu/applications/argocd/rda-pgdb02?view=tree&resource=)
2. Find the `Cluster` resource named `pgdb02`
3. Delete the resource
4. Click "Sync" to recreate it
5. Monitor the logs in ArgoCD

**Option 2: Via kubectl**
```bash
# Delete the cluster
kubectl delete cluster pgdb02 -n rda --context mlc1

# ArgoCD will automatically recreate it on the next sync
# Or manually sync in the ArgoCD UI
```

**Monitoring rebuild progress:**
```bash
# Watch cluster status
kubectl get cluster pgdb02 -n rda --context mlc1 -w

# Get the pg_basebackup pod name (it will have a random suffix)
kubectl get pods -n rda --context mlc1 | grep pgbasebackup

# View pg_basebackup logs (replace with actual pod name from above)
kubectl logs -n rda pgdb02-1-pgbasebackup-xxxxx -f --context mlc1

# Check PVC size growth
kubectl get pvc -n rda --context mlc1 | grep pgdb02

# Watch PVC size in real-time
watch -n 5 'kubectl get pvc -n rda --context mlc1 | grep pgdb02'
```

The rebuild process typically takes several hours depending on database size. The pg_basebackup job runs in a pod with a name like `pgdb02-1-pgbasebackup-xxxxx` (where `xxxxx` is a random suffix). Once the backup completes, the main `pgdb02-1` pod will start and the cluster status will show as "Cluster in healthy state".

### Important Notes
- **Version Compatibility**: pgdb02 must use the same PostgreSQL major version as pgdb01. Currently both run `ghcr.io/cloudnative-pg/postgresql:17.4`
- **Data Loss**: Deleting and rebuilding pgdb02 will resync all data from pgdb01. This is safe for the replica but takes time.