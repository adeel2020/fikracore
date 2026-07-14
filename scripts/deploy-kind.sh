#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${1:-agenticaiops}"

echo "=== Deploy AgenticAIOPs to Kind ==="

# 1. Create cluster
echo "[1/6] Creating kind cluster '$CLUSTER_NAME'..."
kind create cluster --name "$CLUSTER_NAME" --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
      - containerPort: 443
        hostPort: 8443
        protocol: TCP
  - role: worker
EOF

# 2. Install NGINX ingress
echo "[2/6] Installing NGINX ingress controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# 3. Install cert-manager
echo "[3/6] Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml
kubectl wait --namespace cert-manager --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# 4. Install Prometheus stack
echo "[4/6] Installing kube-prometheus-stack..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade --install kube-prometheus bitnami/kube-prometheus \
  --namespace monitoring --create-namespace --wait

# 5. Create namespace and apply platform
echo "[5/6] Deploying platform..."
kubectl create namespace agents-prod --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/network-policies/deny-all-namespaces.yaml
kubectl apply -f deploy/secrets/
kubectl apply -f deploy/network-policies/tier2-nginx-policy.yaml
kubectl apply -f deploy/platform/gateway/
kubectl apply -f deploy/platform/frontend/
kubectl apply -f deploy/infra/postgres/
kubectl apply -f deploy/infra/qdrant/
kubectl apply -f deploy/infra/redis/

# 6. Apply agents
echo "[6/6] Deploying agents..."
kubectl apply -f deploy/kagent/agents.yaml
kubectl apply -f deploy/kagent/gateway.yaml

echo "=== Deploy complete (manual apply) ==="
echo "  Gateway:  http://localhost:8080"
echo ""
echo "To switch to GitOps with ArgoCD:"
echo "  bash deploy/argocd/bootstrap.sh kind"
echo ""
kubectl get pods -n agents-prod
