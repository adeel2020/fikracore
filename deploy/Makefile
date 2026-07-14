# ─── AgenticAIOPs Deployment Makefile ───────────────────────────────────────
# Targets for local (Colima K3s) and production (OpenShift) deployment.
# ────────────────────────────────────────────────────────────────────────────

SHELL := /bin/bash
NAMESPACE := agenticaiops
BACKEND_IMAGE ?= localhost:5000/agenticaiops-backend:v1
FRONTEND_IMAGE ?= localhost:5000/agenticaiops-frontend:v1
CONTROLLER_IMAGE ?= localhost:5000/agenticaiops-controller:v1

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

# ── Container Build & Push ──────────────────────────────────────────────────

.PHONY: registry-start
registry-start: ## Start local Docker registry on port 5000
	docker run -d --name registry --restart always -p 5000:5000 registry:2 || true

.PHONY: build-backend
build-backend: ## Build backend Docker image
	docker build \
		-t $(BACKEND_IMAGE) \
		-f deploy/docker/backend.Dockerfile \
		.
	@echo "Built: $(BACKEND_IMAGE)"

.PHONY: build-frontend
build-frontend: ## Build frontend Docker image
	docker build \
		-t $(FRONTEND_IMAGE) \
		-f deploy/docker/frontend.Dockerfile \
		.
	@echo "Built: $(FRONTEND_IMAGE)"

.PHONY: build-controller
build-controller: ## Build controller Docker image
	docker build \
		-t $(CONTROLLER_IMAGE) \
		-f deploy/controller/Dockerfile \
		.
	@echo "Built: $(CONTROLLER_IMAGE)"

.PHONY: push-local
push-local: ## Push images to local registry
	docker push $(BACKEND_IMAGE)
	docker push $(FRONTEND_IMAGE)
	docker push $(CONTROLLER_IMAGE)

.PHONY: load-colima
load-colima: ## Load images directly into Colima (bypass registry)
	docker save $(BACKEND_IMAGE) -o /tmp/backend.tar
	docker save $(FRONTEND_IMAGE) -o /tmp/frontend.tar
	docker save $(CONTROLLER_IMAGE) -o /tmp/controller.tar
	colima ssh -- docker load -i /tmp/backend.tar
	colima ssh -- docker load -i /tmp/frontend.tar
	colima ssh -- docker load -i /tmp/controller.tar
	rm -f /tmp/backend.tar /tmp/frontend.tar /tmp/controller.tar
	@echo "Loaded images into Colima"

# ── CRD & Controller ────────────────────────────────────────────────────────

.PHONY: deploy-crd
deploy-crd: ## Register the AgentPlatform CRD
	kubectl apply -f deploy/crd/platform.agenticaiops.io_agentplatforms.yaml

.PHONY: deploy-controller
deploy-controller: ## Deploy the kopf controller (RBAC + Deployment)
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f deploy/controller/rbac.yaml
	kubectl apply -f deploy/controller/deployment.yaml
	kubectl wait --for=condition=available deployment/agenticaiops-controller \
		-n $(NAMESPACE) --timeout=60s

.PHONY: deploy-sample
deploy-sample: ## Apply the dev sample CR
	kubectl apply -f deploy/samples/dev.yaml

.PHONY: deploy-all
deploy-all: deploy-crd deploy-controller deploy-sample ## Full deploy: CRD + controller + sample

# ── Infrastructure ──────────────────────────────────────────────────────────

.PHONY: infra-postgres
infra-postgres: ## Deploy PostgreSQL (CloudNativePG)
	kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
	kubectl wait --for=condition=available deployment/cnpg-controller-manager \
		-n cnpg-system --timeout=120s
	@echo "CNPG operator deployed. Create a Cluster CR to start PostgreSQL."

.PHONY: infra-redis
infra-redis: ## Deploy Redis standalone
	kubectl apply -f - < deploy/infra/redis.yaml 2>/dev/null || \
	kubectl apply -f - <<< ''
	kubectl wait --for=condition=available deployment/redis -n $(NAMESPACE) --timeout=60s

.PHONY: infra-argocd
infra-argocd: ## Deploy ArgoCD
	kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
	kubectl wait --for=condition=ready pod \
		-l app.kubernetes.io/name=argocd-server \
		-n argocd --timeout=120s
	@echo "ArgoCD password:"
	@kubectl -n argocd get secret argocd-initial-admin-secret \
		-o jsonpath="{.data.password}" | base64 -d; echo ""

.PHONY: infra-external-secrets
infra-external-secrets: ## Deploy ExternalSecretsOperator
	helm repo add external-secrets https://charts.external-secrets.io
	helm upgrade --install external-secrets external-secrets/external-secrets \
		-n external-secrets --create-namespace
	kubectl wait --for=condition=available deployment/external-secrets-operator \
		-n external-secrets --timeout=60s

.PHONY: infra-all
infra-all: infra-postgres infra-redis infra-argocd infra-external-secrets ## Deploy all infrastructure

# ── Ingress ─────────────────────────────────────────────────────────────────

.PHONY: ingress-traefik
ingress-traefik: ## Create Traefik ingress for platform services
	kubectl apply -f deploy/ingress/traefik.yaml

.PHONY: ingress-argocd
ingress-argocd: ## Create Traefik ingress for ArgoCD
	kubectl apply -f deploy/ingress/argocd.yaml

.PHONY: ingress-all
ingress-all: ingress-traefik ingress-argocd ## Create all ingresses

# ── ArgoCD ──────────────────────────────────────────────────────────────────

.PHONY: argocd-login
argocd-login: ## Login to ArgoCD CLI
	@PASS=$$(kubectl -n argocd get secret argocd-initial-admin-secret \
		-o jsonpath="{.data.password}" | base64 -d); \
	argocd login argocd.localdev.me \
		--username admin \
		--password "$$PASS" \
		--insecure

.PHONY: argocd-project
argocd-project: ## Create the ArgoCD AppProject
	kubectl apply -f deploy/argocd/projects/agenticaiops-project.yaml

.PHONY: argocd-app
argocd-app: ## Create the root ArgoCD Application (App-of-Apps)
	kubectl apply -f deploy/argocd/root-app.yaml

.PHONY: argocd-bootstrap
argocd-bootstrap: infra-argocd argocd-project argocd-app ## Full ArgoCD bootstrap: install + project + apps

# ── Port-Forward ────────────────────────────────────────────────────────────

.PHONY: pf-backend
pf-backend: ## Port-forward backend gateway to :8000
	kubectl port-forward -n $(NAMESPACE) svc/nginx-gateway 8000:8000

.PHONY: pf-frontend
pf-frontend: ## Port-forward frontend to :3000
	kubectl port-forward -n $(NAMESPACE) svc/agenticaiops-frontend 3000:3000

.PHONY: pf-argocd
pf-argocd: ## Port-forward ArgoCD to :8080
	kubectl port-forward svc/argocd-server -n argocd 8080:443

# ── Observability ───────────────────────────────────────────────────────────

.PHONY: logs-controller
logs-controller: ## Tail controller logs
	kubectl logs -n $(NAMESPACE) deployment/agenticaiops-controller -f

.PHONY: logs-agent
logs-agent: ## Tail a specific agent's logs (usage: make logs-agent AGENT=qna)
	kubectl logs -n $(NAMESPACE) deployment/$(AGENT)-agent -f

.PHONY: status
status: ## Show all platform resources
	@echo "=== Deployments ==="
	@kubectl get deployments -n $(NAMESPACE)
	@echo ""
	@echo "=== Services ==="
	@kubectl get services -n $(NAMESPACE)
	@echo ""
	@echo "=== HPAs ==="
	@kubectl get hpa -n $(NAMESPACE)
	@echo ""
	@echo "=== PDBs ==="
	@kubectl get pdb -n $(NAMESPACE)
	@echo ""
	@echo "=== Ingresses ==="
	@kubectl get ingress -n $(NAMESPACE)
	@echo ""
	@echo "=== AgentPlatform CR ==="
	@kubectl get agentplatform -n $(NAMESPACE)

# ── Cleanup ─────────────────────────────────────────────────────────────────

.PHONY: clean-app
clean-app: ## Delete the AgentPlatform CR (controller cleans up child resources)
	kubectl delete agentplatform --all -n $(NAMESPACE) --wait=false

.PHONY: clean-namespace
clean-namespace: ## Delete the platform namespace (deletes everything)
	kubectl delete namespace $(NAMESPACE) --wait=false

.PHONY: clean-crd
clean-crd: ## Delete the CRD
	kubectl delete crd agentplatforms.platform.agenticaiops.io --wait=false

.PHONY: clean-argocd
clean-argocd: ## Delete ArgoCD
	kubectl delete namespace argocd --wait=false

.PHONY: clean-infra
clean-infra: ## Delete infrastructure (CNPG, external-secrets)
	-kubectl delete -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
	-helm uninstall external-secrets -n external-secrets
	-kubectl delete namespace external-secrets
	-kubectl delete namespace cnpg-system

.PHONY: clean-all
clean-all: clean-app clean-namespace clean-crd clean-argocd clean-infra ## Full teardown

.PHONY: clean-registry
clean-registry: ## Stop and remove local registry
	docker stop registry && docker rm registry || true

# ── Quick Start ─────────────────────────────────────────────────────────────

.PHONY: quick-start
quick-start: ## Full quick-start: cluster → build → ArgoCD GitOps
	@echo "=== Step 1: Create cluster ==="
	@echo "    make colima-start        (Colima/K3s)"
	@echo "    — or —"
	@echo "    bash scripts/deploy-kind.sh  (kind)"
	@echo ""
	@echo "=== Step 2: Build & push images ==="
	@echo "    make build-backend build-frontend build-controller push-local"
	@echo "    — or —"
	@echo "    CI pipeline builds + pushes automatically"
	@echo ""
	@echo "=== Step 3: Bootstrap ArgoCD ==="
	@echo "    make argocd-bootstrap"
	@echo ""
	@echo "=== Step 4: Create ingress ==="
	@echo "    make ingress-all && echo '127.0.0.1 api.localdev.me app.localdev.me' | sudo tee -a /etc/hosts"
	@echo ""
	@echo "=== Done ==="
	@echo "ArgoCD UI: make pf-argocd  →  http://localhost:8080"
	@echo "API:       http://api.localdev.me/health"
	@echo ""
	@echo "ArgoCD auto-syncs all apps from deploy/argocd/apps/"
	@echo "Manual sync:  argocd app sync agenticaiops-agents"
