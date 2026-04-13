---
name: infra-gotchas
description: GKE Autopilot spot instance behavior and cold-start timing issues
type: project
---

Cluster runs GKE Autopilot with spot instances (`cloud.google.com/gke-spot=true`). Nodes get preempted regularly by GCP -- this is by design, not OOM. When a spot node is reclaimed, all pods get evicted and rescheduled to new nodes.

**Why this matters:** During a spot preemption on 2026-04-06, cloud-sql-proxy failed to authenticate on the new node (`failed to create default credentials`) because workload identity tokens take a moment to propagate after node creation. The agent pods also failed startup probes (30 failures x 5s = 2.5min limit) because cold starts are slow on fresh spot nodes. Both resolved on their own after ~3 minutes.

**How to apply:** When debugging pod failures, check `kubectl describe node` for spot labels before assuming OOM. Transient cloud-sql-proxy auth failures after node rotation are expected and self-healing. If agent startup probes become a recurring issue, consider increasing the failure threshold.
