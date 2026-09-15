# ─── AgenticAIOPs Deployment Makefile ───────────────────────────────────────
# Pure Helm. Single command to deploy the entire platform.
# ────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
CHART := deploy/charts/agenticaiops

.PHONY: help
help: ## Print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ── Colima ──────────────────────────────────────────────────────────────────

.PHONY: colima-start
colima-start: ## Start Colima with K3s (8GB RAM, 4 CPUs)
	colima start \
		--kubernetes \
		--kubernetes-version v1.30.2 \
		--memory 8 \
		--cpus 4 \
		--disk 50

.PHONY: colima-stop
colima-stop: ## Stop Colima
	colima stop

.PHONY: colima-status
colima-status: ## Show Colima status
	colima status
	kubectl cluster-info
	kubectl get nodes

# ── Deploy ──────────────────────────────────────────────────────────────────

.PHONY: deps
deps: ## Download chart dependencies (argocd, sealed-secrets)
	helm dependency update $(CHART)

.PHONY: deploy
deploy: deps ## Deploy the full platform via Helm
	helm upgrade --install agenticaiops $(CHART) --wait --timeout 10m

.PHONY: deploy-local
deploy-local: ## Deploy with local git daemon (ArgoCD syncs from local repo)
	@echo "Starting git daemon... (run this in another terminal for persistent serving)"
	git daemon --base-path=$$(cd .. && pwd) --export-all --reuseaddr --port=9418 &
	helm upgrade --install agenticaiops $(CHART) \
		--set repoUrl=git://host.docker.internal/kagent \
		--wait --timeout 10m

# ── ArgoCD ──────────────────────────────────────────────────────────────────

.PHONY: argocd-login
argocd-login: ## Login to ArgoCD CLI
	@PASS=$$(kubectl -n argocd get secret argocd-initial-admin-secret \
		-o jsonpath="{.data.password}" | base64 -d); \
	argocd login argocd.localdev.me \
		--username admin \
		--password "$$PASS" \
		--insecure

.PHONY: pf-argocd
pf-argocd: ## Port-forward ArgoCD UI
	kubectl port-forward svc/argocd-server -n argocd 8080:443

# ── Cleanup ─────────────────────────────────────────────────────────────────

.PHONY: clean-argocd
clean-argocd: ## Delete ArgoCD (namespace deletion)
	kubectl delete namespace argocd --wait=false

.PHONY: clean-all
clean-all: ## Delete ArgoCD and agents-prod namespaces (full teardown)
	kubectl delete namespace argocd --wait=false 2>/dev/null || true
	kubectl delete namespace agents-prod --wait=false 2>/dev/null || true
	kubectl delete namespace monitoring --wait=false 2>/dev/null || true
	kubectl delete namespace sealed-secrets --wait=false 2>/dev/null || true

# ── Quick Start ─────────────────────────────────────────────────────────────

.PHONY: quick-start
quick-start: ## Full quick-start: cluster → Helm → ArgoCD GitOps
	@echo "=== Step 1: Start Colima ==="
	@echo "    make colima-start"
	@echo ""
	@echo "=== Step 2: Deploy platform (ArgoCD + All apps) ==="
	@echo "    make deps"
	@echo "    make deploy-local"
	@echo ""
	@echo "=== Step 3: Port-forward ArgoCD UI ==="
	@echo "    make pf-argocd  →  https://localhost:8080"
	@echo ""
	@echo "=== ArgoCD auto-syncs apps from git ==="
	@echo "    Apps: agents, gateway, secops, infra, ingress, rbac, monitoring, network-policies"
	@echo ""
