# Colima K3s Local Setup

Local Kubernetes development environment using Colima with K3s, Traefik ingress, ArgoCD, PostgreSQL (CloudNativePG), Redis, and the AgenticAIOPs controller.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Colima + K3s](#2-install-colima--k3s)
3. [Local Container Registry](#3-local-container-registry)
4. [Deploy the AgentPlatform Controller + CRDs](#4-deploy-the-agentplatform-controller--crds)
5. [Apply a Sample CR](#5-apply-a-sample-cr)
6. [Access Services via Port-Forward](#6-access-services-via-port-forward)
7. [Access via Traefik Ingress](#7-access-via-traefik-ingress)
8. [Install PostgreSQL (CloudNativePG)](#8-install-postgresql-cloudnativepg)
9. [Install Redis](#9-install-redis)
10. [Install ArgoCD](#10-install-argocd)
11. [Create ArgoCD Ingress](#11-create-argocd-ingress)
12. [Login to ArgoCD CLI](#12-login-to-argocd-cli)
13. [Register Repo with ArgoCD](#13-register-repo-with-argocd)
14. [Create Root Application](#14-create-root-application)
15. [Install ExternalSecretsOperator](#15-install-externalsecretsoperator)
16. [Quick Reference](#16-quick-reference)
17. [Teardown](#17-teardown)
18. [Troubleshooting](#18-troubleshooting)

---

## 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Colima | >=0.7 | `brew install colima` |
| Docker | >=24 | `brew install docker` |
| kubectl | >=1.28 | `brew install kubectl` |
| Helm | >=3.14 | `brew install helm` |
| argocd CLI | >=2.10 | `brew install argocd` |

Verify:

```bash
colima version
docker version
kubectl version --client
helm version
argocd version --client
```

---

## 2. Install Colima + K3s

```bash
# Start Colima with K3s (8GB RAM, 4 CPUs recommended for all agents)
colima start \
  --kubernetes \
  --kubernetes-version v1.30.2 \
  --memory 8 \
  --cpus 4 \
  --disk 50

```
## Downloading & installing the kubectl + checksum using CURL
```
Kubectl:

curl -LO "https://dl.k8s.io/release/v1.31.2/bin/darwin/amd64/kubectl" 

checksum file:

curl -LO "https://dl.k8s.io/release/v1.31.2/bin/darwin/amd64/kubectl.sha256"

compare:
echo "$(cat kubectl.sha256)  kubectl" | shasum -a 256 --check
```
### check the colima k8s cluster port & set on main terminal
```
kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://127.0.0.1:50102
  name: default
---------------------------------
kubectl config set-cluster colima \
  --server=https://127.0.0.1:50102
```
```



# Verify the cluster
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# You should see:
#   kube-system    coredns-...
#   kube-system    local-path-provisioner-...
#   kube-system    metrics-server-...
#   kube-system    svclb-traefik-...
#   kube-system    traefik-...
```

> **Note**: K3s ships with Traefik as the default ingress controller and `local-path-provisioner` for dynamic PVCs. No extra addons needed.

---

## 3. Local Container Registry

Choose **one** option:

### Option A: Local registry (recommended for dev)

Lightweight OCI-compliant registry — 40MB, zero config:

```bash
docker run -d \
  --name registry \
  --restart always \
  -p 5000:5000 \
  registry:2

# Verify
curl http://localhost:5000/v2/
```

Build and push images:

```bash
# Backend
docker build \
  -t localhost:5000/agenticaiops-backend:v1 \
  -f deploy/docker/backend.Dockerfile \
  .
docker push localhost:5000/agenticaiops-backend:v1

# Controller
docker build \
  -t localhost:5000/agenticaiops-controller:v1 \
  -f deploy/controller/Dockerfile \
  .
docker push localhost:5000/agenticaiops-controller:v1

# Frontend
docker build \
  -t localhost:5000/agenticaiops-frontend:v1 \
  -f deploy/docker/frontend.Dockerfile \
  .
docker push localhost:5000/agenticaiops-frontend:v1
```

### Option B: Docker Hub

```bash
docker build -t <your-dockerhub>/agenticaiops-backend:v1 .
docker push <your-dockerhub>/agenticaiops-backend:v1
```

### Option C: Quay.io (production target)

```bash
# Create repository via API
curl -X POST https://quay.io/api/v1/repository \
  -H "Authorization: Bearer $QUAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "yourorg",
    "repository": "agenticaiops-backend",
    "visibility": "public"
  }'

# Build and push
docker build -t quay.io/yourorg/agenticaiops-backend:v1 .
docker push quay.io/yourorg/agenticaiops-backend:v1
```

Get `$QUAY_TOKEN` from **Quay.io → Account Settings → Generate Encrypted Password**.

### Push images to Colima's K3s (no registry needed)

For quick testing, you can load images directly into Colima's K3s:

```bash
colima ssh -- docker build -t agenticaiops-backend:v1 -f /Users/adeelarshad/AgenticAIOPs/deploy/docker/backend.Dockerfile /Users/adeelarshad/AgenticAIOPs
```

Or use `k3s ctr image import` (see Troubleshooting section).

---

## 4. Deploy the AgentPlatform Controller + CRDs

All commands from the repository root:

```bash
# Create the namespace
kubectl create namespace agenticaiops

# Register the CRD
kubectl apply -f deploy/crd/platform.agenticaiops.io_agentplatforms.yaml

# Deploy the controller RBAC + Deployment
kubectl apply -f deploy/controller/rbac.yaml
kubectl apply -f deploy/controller/deployment.yaml

# Wait for controller to be ready
kubectl wait --for=condition=available deployment/agenticaiops-controller \
  -n agenticaiops --timeout=60s

# Verify
kubectl get crd | grep platform.agenticaiops.io
kubectl get pods -n agenticaiops
```

Expected output:

```
agentplatforms.platform.agenticaiops.io   2026-07-12T12:00:00Z
NAME                                       READY   STATUS    RESTARTS   AGE
agenticaiops-controller-xxx-yyy            1/1     Running   0          30s
```

---

## 5. Apply a Sample CR

```bash
# Apply the development sample
kubectl apply -f deploy/samples/dev.yaml

# Watch the controller create resources
watch kubectl get deployments,services,hpa,pdb -n agenticaiops
```

Expected output (after ~30s):

```
NAME                                      READY   UP-TO-DATE   AVAILABLE
deployment.apps/qna-agent                 2/2     2            2
deployment.apps/cognitive-agent           1/1     1            1
deployment.apps/complaint-agent           2/2     2            2
deployment.apps/jarvis-agent              1/1     1            1
deployment.apps/nginx-gateway             2/2     2            2
deployment.apps/agenticaiops-frontend     2/2     2            2

NAME                              TYPE        CLUSTER-IP      PORT(S)
service/qna-agent                 ClusterIP   10.43.x.x       8000/TCP
service/cognitive-agent           ClusterIP   10.43.x.x       8000/TCP
service/complaint-agent           ClusterIP   10.43.x.x       8000/TCP
service/jarvis-agent              ClusterIP   10.43.x.x       8000/TCP
service/nginx-gateway             ClusterIP   10.43.x.x       8000/TCP
service/agenticaiops-frontend     ClusterIP   10.43.x.x       3000/TCP

NAME                                      REFERENCE                    TARGETS   MINPODS   MAXPODS
horizontalpodautoscaler.autoscaling/qna   Deployment/qna-agent         0%/70%    2         10

NAME                                      MIN AVAILABLE   MAX UNAVAILABLE
poddisruptionbudget.policy/qna-agent      1               N/A
```

---

## 6. Access Services via Port-Forward

```bash
# Backend gateway
kubectl port-forward -n agenticaiops svc/nginx-gateway 8000:8000 &

# Frontend
kubectl port-forward -n agenticaiops svc/agenticaiops-frontend 3000:3000 &

# PostgreSQL (if needed for direct access)
kubectl port-forward -n agenticaiops svc/pg-cluster-rw 5432:5432 &

# Redis
kubectl port-forward -n agenticaiops svc/redis 6379:6379 &

# Test the backend
curl http://localhost:8000/api/qna/health
```

Expected health response:

```json
{"status": "healthy", "agent": "QnA Assistant"}
```

---

## 7. Access via Traefik Ingress

Traefik is built into K3s. Create an Ingress that routes to the gateway and frontend:

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: platform-ingress
  namespace: agenticaiops
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  ingressClassName: traefik
  rules:
    - host: api.localdev.me
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: nginx-gateway
                port: 8000
    - host: app.localdev.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: agenticaiops-frontend
                port: 3000
EOF
```

Add to `/etc/hosts`:

```bash
echo "127.0.0.1 api.localdev.me app.localdev.me" | sudo tee -a /etc/hosts
```

Test:

```bash
curl http://api.localdev.me/api/qna/health
# Open http://app.localdev.me in browser for frontend
```

### How Traefik Ingress works on K3s

K3s runs Traefik as a DaemonSet listening on ports 80 and 443 (host ports). When you create an `Ingress` resource with `ingressClassName: traefik`, Traefik automatically picks it up and routes traffic based on the `host` and `path` rules. No additional load balancer or MetalLB needed — Colima maps the host ports directly.

Check Traefik:

```bash
kubectl get pods -n kube-system | grep traefik
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik --tail=20
```

---

## 8. Install PostgreSQL (CloudNativePG)

```bash
# Deploy the CloudNativePG operator
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml

# Wait for the operator to be ready
kubectl wait --for=condition=available deployment/cnpg-controller-manager \
  -n cnpg-system --timeout=120s

# Create a Postgres cluster
kubectl apply -f - <<'EOF'
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pg-cluster
  namespace: agenticaiops
spec:
  instances: 1
  storage:
    size: 10Gi
  bootstrap:
    initdb:
      database: agenticaiops
      owner: app
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: "2"
      memory: 4Gi
EOF

# Wait for the cluster to be ready
kubectl wait --for=condition=ready cluster/pg-cluster \
  -n agenticaiops --timeout=120s

# Get the connection credentials
kubectl get secret pg-cluster-app \
  -n agenticaiops \
  -o jsonpath='{.data.uri}' | base64 -d
echo ""

# The URI will look like:
# postgresql://app:<password>@pg-cluster-rw.agenticaiops.svc:5432/agenticaiops
```

### Verify PostgreSQL

```bash
# Connect and run a test query
kubectl run psql-test --rm -it \
  --image=postgres:16-alpine \
  --namespace=agenticaiops \
  -- psql $(kubectl get secret pg-cluster-app -n agenticaiops -o jsonpath='{.data.uri}' | base64 -d) \
  -c "SELECT 'CNPG ready' AS status;"
```

Expected output:

```
  status
-----------
 CNPG ready
(1 row)
```

---

## 9. Install Redis

```bash
kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: agenticaiops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 2Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: agenticaiops
spec:
  ports:
    - port: 6379
  selector:
    app: redis
EOF

# Verify
kubectl wait --for=condition=available deployment/redis -n agenticaiops --timeout=60s
kubectl exec -n agenticaiops deploy/redis -- redis-cli PING
# Should respond: PONG
```

---

## 10. Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Apply the official ArgoCD install manifest
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=120s

# Verify
kubectl get pods -n argocd
```

Expected output:

```
NAME                                                READY   STATUS    RESTARTS
argocd-application-controller-xxx-yyy               1/1     Running   0
argocd-applicationset-controller-xxx-yyy            1/1     Running   0
argocd-dex-server-xxx-yyy                           1/1     Running   0
argocd-notifications-controller-xxx-yyy             1/1     Running   0
argocd-redis-xxx-yyy                                1/1     Running   0
argocd-repo-server-xxx-yyy                          1/1     Running   0
argocd-server-xxx-yyy                               1/1     Running   0
```

### Get the initial admin password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo ""
```

Save this password — you'll need it to log in.

---

## 11. Create ArgoCD Ingress

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd
  namespace: argocd
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  ingressClassName: traefik
  rules:
    - host: argocd.localdev.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
EOF

# Add to /etc/hosts
echo "127.0.0.1 argocd.localdev.me" | sudo tee -a /etc/hosts
```

Access **http://argocd.localdev.me** in your browser.

> **Note**: ArgoCD listens on port 443 (HTTPS). Traefik terminates TLS at the ingress. The UI works over plain HTTP locally since there's no real TLS.

---

## 12. Login to ArgoCD CLI

```bash
# Login using the ingress URL
PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)

argocd login argocd.localdev.me \
  --username admin \
  --password "$PASS" \
  --insecure

# Verify
argocd account get-user-info
```

Expected output:

```
Logged in successfully to 'argocd.localdev.me'
Username: admin
...

User Info:
  User: admin
  ...
```

---

## 13. Register Repo with ArgoCD

ArgoCD needs access to your Git repository containing the `AgentPlatform` CR and deployment configs.

```bash
# For a public repo (no auth needed)
argocd repo add https://github.com/yourorg/agenticaiops-deploy.git

# For a private repo (with token)
argocd repo add https://github.com/yourorg/agenticaiops-deploy.git \
  --username your-github-username \
  --password your-github-token

# Verify
argocd repo list
```

---

## 14. Create Root Application

The root ArgoCD Application syncs the `AgentPlatform` CR from Git, which triggers the kopf controller to generate all child resources.

```bash
kubectl apply -f - <<'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: agenticaiops-platform
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourorg/agenticaiops-deploy.git
    path: overlays/dev
    targetRevision: HEAD
  destination:
    server: https://kubernetes.default.svc
    namespace: agenticaiops
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
EOF
```

### How the GitOps flow works

```
Git Push (update AgentPlatform CR)
  → GitHub webhook triggers ArgoCD sync
    → ArgoCD applies CR to cluster
      → kopf controller detects change
        → reconcilers generate Deployments, Services, HPAs, PDBs, Ingresses
          → K8s API creates/updates resources
```

### Monitor sync

```bash
# Watch the sync status
argocd app get agenticaiops-platform -w

# View sync history
argocd app get agenticaiops-platform --history

# Force manual sync
argocd app sync agenticaiops-platform

# View logs
argocd app logs agenticaiops-platform
```

---

## 15. Install ExternalSecretsOperator

```bash
# Add the helm repo
helm repo add external-secrets https://charts.external-secrets.io

# Install
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --create-namespace

# Wait
kubectl wait --for=condition=available deployment/external-secrets-operator \
  -n external-secrets --timeout=60s

# Create a ClusterSecretStore for local development
# In dev, we use K8s secrets directly (for production, switch to Vault/AWS/GCP)
kubectl apply -f - <<'EOF'
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: local
spec:
  provider:
    kubernetes:
      server:
        url: https://kubernetes.default.svc
EOF

# Create a sample K8s secret that ExternalSecretsOperator can reference
kubectl create secret generic openai-credentials \
  -n agenticaiops \
  --from-literal=api_key=sk-your-api-key-here \
  --from-literal=api_base=https://api.openai.com/v1

# Create an ExternalSecret to test
kubectl apply -f - <<'EOF'
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: qna-agent-secrets
  namespace: agenticaiops
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: local
  target:
    name: qna-agent-secrets
    creationPolicy: Owner
  data:
    - secretKey: OPENAI_API_KEY
      remoteRef:
        key: openai-credentials
        property: api_key
    - secretKey: OPENAI_API_BASE
      remoteRef:
        key: openai-credentials
        property: api_base
EOF

# Verify the secret was created
kubectl get secret qna-agent-secrets -n agenticaiops
kubectl get externalsecret qna-agent-secrets -n agenticaiops -o jsonpath='{.status}' | jq .
```

Expected ExternalSecret status:

```json
{
  "conditions": [
    {
      "type": "Ready",
      "status": "True",
      "reason": "SecretSynced",
      "message": "Secret was synced"
    }
  ],
  "refreshTime": "2026-07-12T12:00:00Z"
}
```

---

## 16. Quick Reference

### Service URLs (via Traefik)

| Service | URL | Auth |
|---------|-----|------|
| ArgoCD UI | `http://argocd.localdev.me` | admin / (from secret) |
| API Gateway | `http://api.localdev.me/api/...` | - |
| Frontend | `http://app.localdev.me` | - |

### Service URLs (via port-forward)

| Service | URL | Auth |
|---------|-----|------|
| ArgoCD | `https://localhost:8080` | admin / (from secret) |
| API Gateway | `http://localhost:8000` | - |
| Frontend | `http://localhost:3000` | - |
| PostgreSQL | `localhost:5432` | cnpg |
| Redis | `localhost:6379` | - |

### Useful commands

```bash
# Watch all pods
kubectl get pods -A -w

# Watch controller logs
kubectl logs -n agenticaiops deployment/agenticaiops-controller -f

# Watch a specific agent
kubectl logs -n agenticaiops deployment/qna-agent -f

# Describe a resource
kubectl describe agentplatform prod -n agenticaiops

# List all generated resources from the CR
kubectl get all -n agenticaiops -l app.kubernetes.io/instance=prod

# Scale an agent manually (HPA will adjust back)
kubectl scale deployment/qna-agent -n agenticaiops --replicas=5

# Trigger re-reconciliation (restart controller)
kubectl rollout restart deployment/agenticaiops-controller -n agenticaiops

# Check HPA status
kubectl get hpa -n agenticaiops -w
```

---

## 17. Teardown

### Full teardown (clean slate)

```bash
# 1. Delete ArgoCD app (stops GitOps sync)
kubectl delete application agenticaiops-platform -n argocd --wait=false

# 2. Delete the AgentPlatform CR (controller cleanup handles child resources via ownerReferences)
kubectl delete agentplatform --all -n agenticaiops --wait=false

# 3. Delete ArgoCD
kubectl delete namespace argocd --wait=false

# 4. Delete platform namespace
kubectl delete namespace agenticaiops --wait=false

# 5. Delete CRD
kubectl delete crd agentplatforms.platform.agenticaiops.io --wait=false

# 6. Delete CNPG operator
kubectl delete -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml --wait=false

# 7. Delete ExternalSecrets
helm uninstall external-secrets -n external-secrets
kubectl delete namespace external-secrets --wait=false

# 8. Stop Colima
colima stop
```

### Partial teardown (keep cluster)

```bash
# Delete just the platform resources
kubectl delete agentplatform --all -n agenticaiops
kubectl delete namespace agenticaiops

# Keep ArgoCD, CNPG, Redis for reuse
```

### Clean up local registry

```bash
docker stop registry && docker rm registry
```

---

## 18. Troubleshooting

### Controller not starting

```bash
# Check logs
kubectl logs -n agenticaiops deployment/agenticaiops-controller

# Common issues:
# - Missing CRD: apply deploy/crd/ first
# - RBAC: check rbac.yaml has correct ClusterRole rules
# - Image pull: check if image exists in registry
```

### ArgoCD sync issues

```bash
# Get detailed sync status
argocd app get agenticaiops-platform
argocd app logs agenticaiops-platform

# Hard refresh (re-fetch from Git)
argocd app sync agenticaiops-platform --force

# Reset app if stuck
argocd app terminate-op agenticaiops-platform
```

### Traefik ingress not routing

```bash
# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik

# Verify ingress exists
kubectl get ingress -n agenticaiops
kubectl describe ingress platform-ingress -n agenticaiops

# Common issues:
# - Missing ingressClassName: ensure it's set to "traefik"
# - Wrong annotation: traefik.ingress.kubernetes.io/router.entrypoints: web
# - Port not forwarded in Colima: colima start should map 80/443
```

### Colima port mapping

```bash
# Check Colima's port forwarding
colima list

# If 80/443 are not forwarded, restart with:
colima stop
colima start --kubernetes --kubernetes-version v1.30.2 --memory 8 --cpus 4

# Or use kubectl port-forward instead of ingress
kubectl port-forward -n agenticaiops svc/nginx-gateway 8000:8000
kubectl port-forward -n agenticaiops svc/agenticaiops-frontend 3000:3000
```

### PostgreSQL not connecting

```bash
# Check CNPG operator status
kubectl get pods -n cnpg-system

# Check cluster status
kubectl describe cluster pg-cluster -n agenticaiops

# Get connection string
kubectl get secret pg-cluster-app -n agenticaiops -o jsonpath='{.data.uri}' | base64 -d

# Test from inside cluster
kubectl run psql-test --rm -it --image=postgres:16-alpine -n agenticaiops -- sh
# Inside the container:
PGPASSWORD=$(kubectl get secret pg-cluster-app -n agenticaiops -o jsonpath='{.data.password}' | base64 -d)
psql -h pg-cluster-rw -U app -d agenticaiops -c "SELECT 1"
```

### Pods stuck in ImagePullBackOff

```bash
# Check the error
kubectl describe pod <pod-name> -n agenticaiops

# If using localhost:5000, make sure the registry container runs on the Docker host
docker ps | grep registry

# If using Quay.io or Docker Hub, make sure the image was pushed
# For local registry, you may need to push images directly into Colima:
colima ssh -- docker pull localhost:5000/agenticaiops-backend:v1
```

### Loading images directly into Colima

If you don't want to run a separate registry, load images directly:

```bash
# Save the image as a tar file
docker save agenticaiops-backend:v1 -o /tmp/backend.tar

# Copy into Colima
colima ssh -- docker load -i /tmp/backend.tar
```

Then update your Deployment's `imagePullPolicy` to `IfNotPresent`:

```yaml
spec:
  template:
    spec:
      containers:
        - image: agenticaiops-backend:v1
          imagePullPolicy: IfNotPresent
```

### Port conflict

If default ports are in use:

```bash
# Change port-forward to different local ports
kubectl port-forward -n agenticaiops svc/nginx-gateway 9000:8000
kubectl port-forward -n agenticaiops svc/agenticaiops-frontend 9001:3000

# Or stop the conflicting process
lsof -i :8000
kill -9 <PID>
```

### HPA not scaling

```bash
# Check HPA status
kubectl describe hpa qna-agent -n agenticaiops

# Common issues:
# - metrics-server not running (should be installed with K3s)
# - CPU requests not set on containers
# - Target too high — lower targetCPU in the CR

# Check metrics-server
kubectl get pods -n kube-system | grep metrics-server
kubectl top pods -n agenticaiops
```

### Re-applying CR after manual changes

If you manually edited a resource and the controller is stuck, you can force re-reconciliation:

```bash
# Annotate the CR to trigger re-reconcile
kubectl annotate agentplatform prod -n agenticaiops \
  platform.agenticaiops.io/reconcile=$(date +%s) --overwrite

# Or restart the controller
kubectl rollout restart deployment/agenticaiops-controller -n agenticaiops
```

---

## Appendix A: How HPA and PDB Work

### HorizontalPodAutoscaler (HPA)

The HPA automatically scales the number of agent pod replicas based on CPU utilization:

```
CPU > 70% ──► add replicas (up to max)
CPU < 50% ──► remove replicas (down to min)
```

Generated per agent from `spec.agents[*].replicas`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: qna-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: qna-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### PodDisruptionBudget (PDB)

The PDB ensures a minimum number of agent pods stay available during voluntary disruptions (node drains, rolling updates, cluster upgrades):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: qna-agent-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/instance: qna-agent
```

With `minAvailable: 1` and `minReplicas: 2`, at most 1 pod can be disrupted at a time — your agent stays available during maintenance.

---

## Appendix B: Agent Scaling Matrix

| Agent | Min | Max | CPU Target | PDB |
|-------|-----|-----|-----------|-----|
| QnA | 2 | 10 | 70% | minAvailable: 1 |
| Cognitive | 1 | 5 | 80% | minAvailable: 1 |
| Complaint | 2 | 8 | 75% | minAvailable: 1 |
| JARVIS | 1 | 3 | 80% | minAvailable: 1 |
| Gateway (nginx) | 2 | 5 | 70% | minAvailable: 1 |
| Frontend | 2 | 5 | 70% | minAvailable: 1 |

---

## Appendix C: Resource Requirements

| Agent | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------|-------------|-----------|----------------|--------------|
| QnA | 500m | 2 | 1Gi | 4Gi |
| Cognitive | 1 | 4 | 2Gi | 8Gi |
| Complaint | 500m | 2 | 1Gi | 4Gi |
| JARVIS | 2 | 4 | 4Gi | 16Gi |
| Gateway (nginx) | 250m | 1 | 512Mi | 2Gi |
| Frontend | 250m | 1 | 512Mi | 2Gi |
| PostgreSQL | 500m | 2 | 1Gi | 4Gi |
| Redis | 250m | 1 | 512Mi | 2Gi |
| Controller | 100m | 500m | 128Mi | 512Mi |
| ArgoCD | 250m | 1 | 512Mi | 2Gi |

**Total minimum for dev**: ~6 CPU, ~12GB memory — fits in 8 CPU / 16GB Colima with headroom.
