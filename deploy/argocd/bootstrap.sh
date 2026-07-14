#!/usr/bin/env bash
# Bootstraps ArgoCD on an existing cluster and deploys AgenticAIOPs via GitOps.
# Usage:
#   ./deploy/argocd/bootstrap.sh                  # remote git repo
#   ./deploy/argocd/bootstrap.sh kind             # kind cluster + remote git
#   ./deploy/argocd/bootstrap.sh --local          # local-only (starts git daemon)
#   ./deploy/argocd/bootstrap.sh kind --local     # kind cluster + local git daemon
set -euo pipefail

CLUSTER_NAME=""
LOCAL_MODE=false
for arg in "$@"; do
  case "$arg" in
    --local) LOCAL_MODE=true ;;
    *)       CLUSTER_NAME="$arg" ;;
  esac
done

ARGOCD_NS="argocd"
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "https://github.com/adeelarshad/kagent")
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== AgenticAIOPs — ArgoCD Bootstrap ==="
echo "Mode:     $([ "$LOCAL_MODE" = true ] && echo 'LOCAL (git daemon)' || echo 'REMOTE')"
echo "Repo:     $REPO_URL"
echo "Branch:   main"
echo ""

# ── Prerequisites ────────────────────────────────────────────────────
for cmd in kubectl helm curl; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd not found. Install it first."
    exit 1
  fi
done

# ── Local mode: start git daemon ─────────────────────────────────────
GIT_DAEMON_PID=""
if [ "$LOCAL_MODE" = true ]; then
  if ! command -v git &>/dev/null; then
    echo "ERROR: git not found."
    exit 1
  fi
  # pods in Colima/kind/Docker-Desktop reach the macOS host via this address
  GIT_HOST="host.docker.internal"
  REPO_URL="git://$GIT_HOST/kagent"
  echo "[pre] Starting git daemon on port 9418 serving $REPO_ROOT ..."
  git daemon --base-path="$REPO_ROOT/.." --export-all --reuseaddr --verbose \
    --port=9418 &
  GIT_DAEMON_PID=$!
  sleep 1
  echo "      git daemon PID $GIT_DAEMON_PID — serving repo at $REPO_URL"
  echo ""

  # Cleanup git daemon on exit
  cleanup() {
    [ -n "$GIT_DAEMON_PID" ] && kill "$GIT_DAEMON_PID" 2>/dev/null && echo "git daemon stopped"
  }
  trap cleanup EXIT
fi

# ── Optional: create kind cluster ────────────────────────────────────
if [ "$CLUSTER_NAME" = "kind" ]; then
  if ! command -v kind &>/dev/null; then
    echo "ERROR: kind not found."
    exit 1
  fi
  echo "[1/4] Creating kind cluster 'agenticaiops'..."
  kind create cluster --name agenticaiops --config - <<EOF
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
      - containerPort: 443
        hostPort: 8443
  - role: worker
EOF

  echo "[2/4] Installing NGINX ingress controller..."
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
  kubectl wait --namespace ingress-nginx --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller --timeout=120s

  echo "[3/4] Installing cert-manager..."
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml
  kubectl wait --namespace cert-manager --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller --timeout=120s
  STEP_OFFSET=3
else
  echo "[1/3] Using existing cluster: $(kubectl config current-context 2>/dev/null || echo 'unknown')"
  STEP_OFFSET=0
fi

# ── Install ArgoCD ──────────────────────────────────────────────────
echo "[$((STEP_OFFSET + 1))/3] Installing ArgoCD..."
kubectl create namespace "$ARGOCD_NS" --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n "$ARGOCD_NS" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --namespace "$ARGOCD_NS" --for=condition=ready pod \
  --selector=app.kubernetes.io/name=argocd-server --timeout=180s

# ── Apply ArgoCD manifests ──────────────────────────────────────────
echo "[$((STEP_OFFSET + 2))/3] Applying AppProject..."
kubectl apply -f deploy/argocd/projects/agenticaiops-project.yaml

echo "[$((STEP_OFFSET + 3))/3] Applying Root App (App-of-Apps)..."
sed "s|repoURL:.*|repoURL: \"$REPO_URL\"|" deploy/argocd/root-app.yaml | kubectl apply -f -

# ── Post-install: add git:// protocol to project sourceRepos ────────
if [ "$LOCAL_MODE" = true ]; then
  echo "[post] Adding git:// protocol to AppProject sourceRepos..."
  kubectl patch appproject agenticaiops -n "$ARGOCD_NS" --type=json \
    -p='[{"op":"add","path":"/spec/sourceRepos/-","value":"git://*"}]' 2>/dev/null || true
fi

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo "=== Bootstrap complete ==="
echo ""
echo "ArgoCD UI:  kubectl port-forward svc/argocd-server -n $ARGOCD_NS 8443:443"
echo "  Username: admin"
echo -n "  Password: "
kubectl -n "$ARGOCD_NS" get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "(wait 30s for secret)"
echo ""
echo "Watch sync:  argocd app sync agenticaiops-secops"
echo "             argocd app sync agenticaiops-agents"
echo "             argocd app sync agenticaiops-gateway"
echo "Get status:  argocd app list"
