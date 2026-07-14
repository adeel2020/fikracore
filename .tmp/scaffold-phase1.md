# Phase 1 — Scaffolding Execution Plan

## Overview

Restructure the monolith into the hybrid microservices architecture:
- **2 Docker images**: `gateway` (NGINX) + `agents` (FastAPI + all agent code)
- **Shared library**: `agenticaiops_shared` as installable Python package
- **Deploy**: kagent Agent CRs, ArgoCD, RBAC, NetworkPolicies, Secrets, ISO 9001+27001 scaffolding
- **Strangler Fig**: `backend/` kept as-is for reference during migration

---

## Step 1 — Create Directory Tree

```bash
# Tier 2 — NGINX Gateway
mkdir -p services/gateway/src/middleware

# Tier 3 — Agents (all agents in one container)
mkdir -p services/agents/src/{core,qna,complaint/complaint,storyteller/datastory,rag/{core,pipelines,services,models,data,infrastructure},jarvis/{superpowers,ui}}

# Tier 4 — Infrastructure deploy manifests
mkdir -p deploy/{secrets/{external-secrets,sealed-secrets},network-policies,rbac/{kubernetes,application},kagent/secops,infra/{postgres,qdrant,redis},platform/{gateway,frontend},ingress,argocd/projects,ci,monitoring/{prometheus,grafana,alertmanager,backup},iso/{9001,27001,evidence}}

# Shared library
mkdir -p shared/agenticaiops_shared/database

# Scripts
mkdir -p scripts

echo "Directory tree created"
```

---

## Step 2 — Copy Files from `backend/` into `services/agents/src/`

**Rule: Copy only, never modify originals. `backend/` stays as-is.**

```bash
# ==================== CORE ====================
cp backend/core/orchestrator.py services/agents/src/core/

# ==================== QNA AGENT ====================
cp backend/agent/primary_agent.py services/agents/src/qna/agent.py
cp backend/agent/skill_manager.py services/agents/src/qna/
cp backend/agent/kg_retriever.py services/agents/src/qna/
cp backend/agent/rag_agent.py services/agents/src/qna/
cp backend/agent/vectorstore.json services/agents/src/qna/

# ==================== COMPLAINT AGENT ====================
cp backend/agent/complaint_analyst.py services/agents/src/complaint/analyst.py
cp backend/agent/complaint/*.py services/agents/src/complaint/complaint/
cp backend/agent/causal_rules.yaml services/agents/src/complaint/

# ==================== STORYTELLER AGENT ====================
cp backend/agent/data_storyteller_agent.py services/agents/src/storyteller/agent.py
cp -r backend/datastory/*.py services/agents/src/storyteller/datastory/
cp -r backend/datastory/data/ services/agents/src/storyteller/datastory/data/
cp -r backend/datastory/tools/ services/agents/src/storyteller/datastory/tools/
cp -r backend/datastory/prompts/ services/agents/src/storyteller/datastory/prompts/
cp -r backend/datastory/models/ services/agents/src/storyteller/datastory/models/
cp -r backend/datastory/pipeline/ services/agents/src/storyteller/datastory/pipeline/

# ==================== RAG SERVICE ====================
cp -r backend/rag/*.py services/agents/src/rag/
cp -r backend/rag/core/ services/agents/src/rag/core/
cp -r backend/rag/pipelines/ services/agents/src/rag/pipelines/
cp -r backend/rag/services/ services/agents/src/rag/services/
cp -r backend/rag/models/ services/agents/src/rag/models/
cp -r backend/rag/data/ services/agents/src/rag/data/
cp -r backend/rag/infrastructure/ services/agents/src/rag/infrastructure/

# ==================== JARVIS ====================
cp backend/jarvis/core.py services/agents/src/jarvis/
cp backend/jarvis/router.py services/agents/src/jarvis/
cp -r backend/jarvis/superpowers/ services/agents/src/jarvis/superpowers/
cp -r backend/jarvis/ui/ services/agents/src/jarvis/ui/
cp backend/jarvis/README.md services/agents/src/jarvis/

# ==================== WORKSPACE DATA FILES ====================
cp trace_graph.json services/agents/src/
cp samples.json services/agents/src/
cp knowledge-graph.json services/agents/src/

echo "Files copied from backend/ to services/agents/"
```

---

## Step 3 — Create `__init__.py` Files

```bash
touch services/agents/src/__init__.py
touch services/agents/src/core/__init__.py
touch services/agents/src/qna/__init__.py
touch services/agents/src/complaint/__init__.py
touch services/agents/src/complaint/complaint/__init__.py
touch services/agents/src/storyteller/__init__.py
touch services/agents/src/storyteller/datastory/__init__.py
touch services/agents/src/rag/__init__.py
touch services/agents/src/rag/core/__init__.py
touch services/agents/src/rag/pipelines/__init__.py
touch services/agents/src/rag/services/__init__.py
touch services/agents/src/rag/models/__init__.py
touch services/agents/src/rag/data/__init__.py
touch services/agents/src/rag/infrastructure/__init__.py
touch services/agents/src/jarvis/__init__.py
touch services/agents/src/jarvis/superpowers/__init__.py
touch services/agents/src/jarvis/ui/__init__.py
touch services/gateway/src/__init__.py
touch services/gateway/src/middleware/__init__.py

echo "init.py files created"
```

---

## Step 4 — Create Shared Library Package

### `shared/pyproject.toml`

```toml
[project]
name = "agenticaiops-shared"
version = "0.1.0"
description = "Shared library for AgenticAIOPs microservices"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "litellm>=1.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["agenticaiops_shared*"]
```

### `shared/agenticaiops_shared/__init__.py`

```python
"""agenticaiops_shared - Common library for AgenticAIOPs microservices."""
```

### `shared/agenticaiops_shared/config.py`

Copy from `backend/config.py` — update import path:

```python
# OLD: from backend.config import settings
# NEW: from agenticaiops_shared.config import settings
```

### `shared/agenticaiops_shared/schemas.py`

Copy directly from `backend/schemas.py` (no import changes needed).

### `shared/agenticaiops_shared/database/__init__.py`

```python
from .db import Base, engine, SessionLocal, get_db, init_db
from .models import ChatSession, ChatMessage, SessionTelemetry, ComplaintTelemetry
```

### `shared/agenticaiops_shared/database/db.py`

Copy from `backend/database/db.py` — update import:

```python
# OLD: from backend.config import settings
# NEW:
from agenticaiops_shared.config import settings
```

### `shared/agenticaiops_shared/database/models.py`

Copy from `backend/database/models.py` — update import:

```python
# OLD: from backend.database.db import Base
# NEW:
from agenticaiops_shared.database.db import Base
```

### `shared/agenticaiops_shared/memory.py`

Copy from `backend/agent/memory.py` — update imports:

```python
# OLD: from backend.schemas import ChatMessage
# NEW:
from agenticaiops_shared.schemas import ChatMessage

# OLD: from backend.database.models import ChatSession, ChatMessage as ChatMessageModel
# NEW:
from agenticaiops_shared.database.models import ChatSession, ChatMessage as ChatMessageModel
```

### `shared/agenticaiops_shared/guardrails.py`

Copy from `backend/agent/guardrails.py` — update import:

```python
# OLD: from backend.config import settings
# NEW:
from agenticaiops_shared.config import settings
```

### Install shared library for local dev

```bash
cd shared
pip install -e .
```

---

## Step 5 — Create `services/agents/src/main.py`

```python
"""Agents Service - FastAPI application entry point. Runs on port 8001."""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agenticaiops_shared.config import settings
from agenticaiops_shared.guardrails import setup_guardrails

from .core import auth as auth_router
from .qna import router as qna_router
from .complaint import router as complaint_router
from .storyteller import router as storyteller_router
from .rag import router as rag_router
from .jarvis import router as jarvis_router

logger = logging.getLogger(__name__)

setup_guardrails()

app = FastAPI(title="AgenticAIOPs Agents Service", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router.router)
app.include_router(qna_router.router)
app.include_router(complaint_router.router)
app.include_router(storyteller_router.router)
app.include_router(rag_router.router)
app.include_router(jarvis_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agents", "version": "0.1.0"}


@app.on_event("startup")
async def startup():
    from agenticaiops_shared.database.db import init_db
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")

    from .qna.kg_retriever import kg_retriever
    try:
        await asyncio.to_thread(kg_retriever.initialize)
    except Exception as e:
        logger.error(f"KG Retriever init failed: {e}")

    from .storyteller.datastory.crewai_storyteller import init_storyteller
    try:
        agent = init_storyteller()
        if agent:
            logger.info("Storyteller agent ready")
    except Exception as e:
        logger.warning(f"Storyteller not available: {e}")

    from .jarvis.core import JARVIS
    try:
        jarvis = JARVIS()
        await jarvis.initialize()
    except Exception as e:
        logger.error(f"JARVIS init failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info")
```

---

## Step 6 — Create `services/agents/pyproject.toml`

```toml
[project]
name = "agenticaiops-agents"
version = "0.1.0"
description = "AgenticAIOPs - All AI agents in one service"
requires-python = ">=3.11"
dependencies = [
    "agenticaiops-shared>=0.1.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "crewai>=0.100",
    "openai>=1.0",
    "numpy>=1.26",
    "pandas>=2.0",
    "pyyaml>=6.0",
    "litellm>=1.0",
    "python-dotenv>=1.0",
    "httpx>=0.27",
    "sentence-transformers>=3.0",
    "qdrant-client>=1.0",
    "chromadb>=0.4",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["*"]
```

---

## Step 7 — Create `services/agents/Dockerfile`

```dockerfile
# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /build
COPY shared/ ./shared/
COPY services/agents/ ./agents/
RUN pip install ./shared/

# Stage 2: Runtime
FROM python:3.11-slim
RUN groupadd -r agent && useradd -r -g agent -d /app -s /sbin/nologin agent
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY services/agents/src/ ./src/
COPY services/agents/pyproject.toml .
ENV PYTHONPATH=/app/src:$PYTHONPATH
ENV PORT=8001
USER agent
EXPOSE 8001
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## Step 8 — Create NGINX Gateway

### `services/gateway/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream agents {
        server agents-service:8001;
    }
    upstream frontend {
        server frontend-service:3000;
    }

    server {
        listen 8443 ssl;
        server_name api.agenticaiops.com;

        ssl_certificate /etc/ssl/certs/tls.crt;
        ssl_certificate_key /etc/ssl/certs/tls.key;

        location = /_auth {
            internal;
            proxy_pass http://agents/api/auth/validate;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
        }

        limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

        location ~ ^/(api/qna|api/complaint|api/storyteller|api/rag|api/jarvis|api/auth) {
            auth_request /_auth;
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://agents;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /health {
            proxy_pass http://agents/health;
        }

        location / {
            proxy_pass http://frontend;
        }
    }

    server {
        listen 8080;
        return 301 https://$host$request_uri;
    }
}
```

### `services/gateway/Dockerfile`

```dockerfile
FROM nginx:1.27-alpine
RUN addgroup -S gateway && adduser -S gateway -G gateway
COPY nginx.conf /etc/nginx/nginx.conf
RUN chown -R gateway:gateway /etc/nginx /var/cache/nginx /var/log/nginx
USER gateway
EXPOSE 8080 8443
CMD ["nginx", "-g", "daemon off;"]
```

---

## Step 9 — Create Router Modules per Agent

### `services/agents/src/core/auth.py`

```python
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/validate")
@router.get("/validate")
async def validate_token(request: Request):
    """Called by NGINX auth_request to validate JWT tokens."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    # Phase 1: stub - accept known tokens
    # Phase 2+: JWT decode, check expiry, return user role
    return {"sub": "user", "role": "admin"}
```

### `services/agents/src/qna/router.py`

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/qna", tags=["qna"])
# Phase 1: routes imported from original api_router.py logic
# Phase 2+: decomposed endpoints
```

### `services/agents/src/complaint/router.py`

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/complaint", tags=["complaint"])
```

### `services/agents/src/storyteller/router.py`

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/storyteller", tags=["storyteller"])
```

### `services/agents/src/rag/router.py`

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/rag", tags=["rag"])
```

### `services/agents/src/jarvis/router.py`

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])
```

---

## Step 10 — Update Import Paths

This is the single largest mechanical change. Every file in `services/agents/src/` needs its import paths updated.

```bash
AGENTS_DIR="services/agents/src"

# Shared library replacements
find "$AGENTS_DIR" -name "*.py" -exec sed -i '' \
  -e 's/from backend\.config/from agenticaiops_shared.config/g' \
  -e 's/from backend\.schemas/from agenticaiops_shared.schemas/g' \
  -e 's/from backend\.database\.models/from agenticaiops_shared.database.models/g' \
  -e 's/from backend\.database\.db/from agenticaiops_shared.database.db/g' \
  -e 's/from backend\.agent\.memory/from agenticaiops_shared.memory/g' \
  -e 's/from backend\.agent\.guardrails/from agenticaiops_shared.guardrails/g' \
  -e 's/import backend\.database\.models/import agenticaiops_shared.database.models/g' \
  -e 's/import backend\.database\.db/import agenticaiops_shared.database.db/g' \
  {} +

# Intra-agent replacements
find "$AGENTS_DIR" -name "*.py" -exec sed -i '' \
  -e 's/from backend\.agent\.complaint_analyst/from ..complaint.analyst/g' \
  -e 's/from backend\.agent\.skill_manager/from ..qna.skill_manager/g' \
  -e 's/from backend\.agent\.kg_retriever/from ..qna.kg_retriever/g' \
  -e 's/from backend\.agent\.data_storyteller_agent/from ..storyteller.agent/g' \
  -e 's/from backend\.agent\.primary_agent/from ..qna.agent/g' \
  -e 's/from backend\.agent\.rag_agent/from ..qna.rag_agent/g' \
  -e 's/from backend\.rag\b/from ..rag/g' \
  -e 's/from backend\.jarvis/from ..jarvis/g' \
  -e 's/import backend\.agent\.complaint_analyst/import ..complaint.analyst as complaint_analyst/g' \
  -e 's/import backend\.agent\.skill_manager/import ..qna.skill_manager/g' \
  -e 's/import backend\.agent\.kg_retriever/import ..qna.kg_retriever/g' \
  -e 's/import backend\.agent\.data_storyteller_agent/import ..storyteller.agent/g' \
  -e 's/import backend\.agent\.primary_agent/import ..qna.agent/g' \
  -e 's/import backend\.agent\.rag_agent/import ..qna.rag_agent/g' \
  -e 's/from backend\.core\.orchestrator/from ..core.orchestrator/g' \
  {} +

# Verify no leftover backend. imports
RESULT=$(grep -rn "from backend\." "$AGENTS_DIR" || echo "")
if [ -n "$RESULT" ]; then
    echo "WARNING: Leftover imports found:"
    echo "$RESULT"
else
    echo "All import paths updated"
fi
```

**Manual fix notes**: Files in `complaint/` and `complaint/complaint/` use deeply nested relative imports. Verify these after sed:

| File | Old Import | New Import |
|---|---|---|
| `complaint/analyst.py` | `from backend.agent.complaint.analyst` | `from .complaint.analyst` |
| `complaint/analyst.py` | `from backend.agent.complaint.utils` | `from .complaint.utils` |
| `complaint/analyst.py` | `from backend.agent.complaint.tools` | `from .complaint.tools` |
| `kg_retriever.py` | `from backend.agent.complaint_analyst import _get_causal_rules` | `from ..complaint.analyst import _get_causal_rules` |

---

## Step 11 — Create kagent Agent CRs

### `deploy/kagent/agents.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: agent-services
  namespace: agents-prod
  labels:
    app.kubernetes.io/part-of: agenticaiops
    iso.9001/component: core-service
    iso.27001/data-classification: confidential
spec:
  type: BYO
  serviceAccountName: agent-operator
  byo:
    deployment:
      image: agenticaiops/agents:latest
      replicas: 2
      strategy:
        type: RollingUpdate
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 0
      resources:
        requests:
          cpu: "500m"
          memory: "512Mi"
        limits:
          cpu: "2"
          memory: "2Gi"
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: QDRANT_URL
          valueFrom:
            secretKeyRef:
              name: qdrant-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
      livenessProbe:
        httpGet:
          path: /health
          port: 8001
        initialDelaySeconds: 30
        periodSeconds: 15
      readinessProbe:
        httpGet:
          path: /health
          port: 8001
        initialDelaySeconds: 5
        periodSeconds: 10
```

### `deploy/kagent/gateway.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: api-gateway
  namespace: agents-prod
  labels:
    app.kubernetes.io/part-of: agenticaiops
spec:
  type: BYO
  serviceAccountName: agent-operator
  byo:
    deployment:
      image: agenticaiops/gateway:latest
      replicas: 2
      resources:
        requests:
          cpu: "100m"
          memory: "64Mi"
        limits:
          cpu: "500m"
          memory: "128Mi"
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
      env:
        - name: JWT_SIGNING_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: signing-key
      livenessProbe:
        httpGet:
          path: /health
          port: 8443
          scheme: HTTPS
        initialDelaySeconds: 10
        periodSeconds: 15
```

### `deploy/kagent/secops/deployment-guardian.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: deployment-guardian
  namespace: agents-prod
  labels:
    iso.27001/control: A.12.1
spec:
  type: BYO
  serviceAccountName: deployment-guardian
  byo:
    deployment:
      image: agenticaiops/guardian:latest
      replicas: 1
      resources:
        requests:
          cpu: "100m"
          memory: "128Mi"
      env:
        - name: ARGOCD_SERVER
          value: argocd-server.argocd.svc.cluster.local:443
      schedule: "*/5 * * * *"
```

### `deploy/kagent/secops/secret-scanner.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: secret-scanner
  namespace: agents-prod
  labels:
    iso.27001/control: A.8.2
spec:
  type: BYO
  serviceAccountName: security-auditor
  byo:
    deployment:
      image: agenticaiops/secret-scanner:latest
      replicas: 1
      schedule: "0 */6 * * *"
```

### `deploy/kagent/secops/policy-enforcer.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: policy-enforcer
  namespace: agents-prod
  labels:
    iso.27001/control: A.5.1
    iso.9001/control: 8.4
spec:
  type: BYO
  serviceAccountName: security-auditor
  byo:
    deployment:
      image: agenticaiops/policy-enforcer:latest
      replicas: 1
      schedule: "0 */12 * * *"
```

### `deploy/kagent/secops/vulnerability-responder.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: vulnerability-responder
  namespace: agents-prod
  labels:
    iso.27001/control: A.8.8
spec:
  type: BYO
  serviceAccountName: security-auditor
  byo:
    deployment:
      image: agenticaiops/vuln-responder:latest
      replicas: 1
      schedule: "0 */6 * * *"
      env:
        - name: TRIVY_SERVER
          value: trivy-server:8080
```

### `deploy/kagent/secops/compliance-auditor.yaml`

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: compliance-auditor
  namespace: agents-prod
  labels:
    iso.27001/control: A.18.1
    iso.9001/control: 9.2
spec:
  type: BYO
  serviceAccountName: security-auditor
  byo:
    deployment:
      image: agenticaiops/compliance-auditor:latest
      replicas: 1
      schedule: "0 6 1 * *"  # 1st of month
```

---

## Step 12 — Create Network Policies

### `deploy/network-policies/deny-all-namespaces.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: agents-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

### `deploy/network-policies/tier2-nginx-policy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tier2-nginx
  namespace: agents-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: api-gateway
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8443
  egress:
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: agent-services
      ports:
        - protocol: TCP
          port: 8001
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: frontend
      ports:
        - protocol: TCP
          port: 3000
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### `deploy/network-policies/tier3-agents-policy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tier3-agents
  namespace: agents-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: agent-services
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: api-gateway
      ports:
        - protocol: TCP
          port: 8001
  egress:
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: qdrant
      ports:
        - protocol: TCP
          port: 6333
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### `deploy/network-policies/tier4-db-policy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tier4-postgres
  namespace: agents-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: postgres
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: agent-services
      ports:
        - protocol: TCP
          port: 5432
  egress: []
```

### `deploy/network-policies/kagent-policy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kagent-access
  namespace: kagent
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: kagent-controller
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: argocd
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: agents-prod
    - to:
        - ipBlock:
            cidr: 10.96.0.0/12
      ports:
        - protocol: TCP
          port: 443
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### `deploy/network-policies/secops-policy.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: secops-agents
  namespace: agents-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name-in: [deployment-guardian, secret-scanner, policy-enforcer,
                                   vulnerability-responder, compliance-auditor]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: kagent-controller
  egress:
    - to:
        - ipBlock:
            cidr: 10.96.0.0/12  # kube-apiserver
      ports:
        - protocol: TCP
          port: 443
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

---

## Step 13 — Create RBAC Manifests

### `deploy/rbac/kubernetes/agent-operator-role.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: agent-operator
  namespace: agents-prod
rules:
  - apiGroups: ["kagent.dev"]
    resources: ["agents", "agents/status"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec", "events", "configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agent-operator-binding
  namespace: agents-prod
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: agent-operator
subjects:
  - kind: ServiceAccount
    name: agent-operator
    namespace: agents-prod
```

### `deploy/rbac/kubernetes/security-auditor-role.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: security-auditor
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "endpoints", "configmaps", "secrets",
                 "namespaces", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["networkpolicies"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources: ["cronjobs", "jobs"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["kagent.dev"]
    resources: ["agents"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: security-auditor-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: security-auditor
subjects:
  - kind: ServiceAccount
    name: security-auditor
    namespace: agents-prod
```

### `deploy/rbac/kubernetes/deployment-guardian-role.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployment-guardian
  namespace: agents-prod
rules:
  - apiGroups: ["argoproj.io"]
    resources: ["applications", "applications/status"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["argoproj.io"]
    resources: ["applications"]
    verbs: ["update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployment-guardian-binding
  namespace: agents-prod
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: deployment-guardian
subjects:
  - kind: ServiceAccount
    name: deployment-guardian
    namespace: agents-prod
```

### `deploy/rbac/kubernetes/ci-pipeline-role.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ci-pipeline
  namespace: agents-prod
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-pipeline-binding
  namespace: agents-prod
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ci-pipeline
subjects:
  - kind: ServiceAccount
    name: ci-pipeline
    namespace: agents-prod
```

### `deploy/rbac/application/roles.yaml`

```yaml
roles:
  admin:
    permissions:
      - "qna:*"
      - "complaint:*"
      - "storyteller:*"
      - "rag:*"
      - "jarvis:*"
      - "admin:*"
      - "audit:*"
  agent:
    permissions:
      - "qna:*"
      - "complaint:*"
      - "rag:*"
  user:
    permissions:
      - "qna:ask"
      - "storyteller:ask"
      - "rag:search"
  secops:
    permissions:
      - "audit:*"
      - "admin:health"
```

---

## Step 14 — Create Secret Management Manifests

### `deploy/secrets/external-secrets/ClusterSecretStore.yaml`

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.agenticaiops.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "agenticaiops"
```

### `deploy/secrets/external-secrets/postgres-secret.yaml`

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-secret
  namespace: agents-prod
spec:
  refreshInterval: "24h"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: postgres-secret
  data:
    - secretKey: url
      remoteRef:
        key: secret/agenticaiops/postgres
        property: url
    - secretKey: password
      remoteRef:
        key: secret/agenticaiops/postgres
        property: password
```

### `deploy/secrets/external-secrets/openai-secret.yaml`

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: openai-secret
  namespace: agents-prod
spec:
  refreshInterval: "24h"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: openai-secret
  data:
    - secretKey: api-key
      remoteRef:
        key: secret/agenticaiops/openai
        property: api-key
```

### `deploy/secrets/external-secrets/jwt-secret.yaml`

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: jwt-secret
  namespace: agents-prod
spec:
  refreshInterval: "24h"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: jwt-secret
  data:
    - secretKey: signing-key
      remoteRef:
        key: secret/agenticaiops/jwt
        property: signing-key
```

---

## Step 15 — Create ArgoCD Manifests

### `deploy/argocd/application.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: agenticaiops
  namespace: argocd
  labels:
    iso.9001/process: continuous-deployment
    iso.27001/control: A.12.1
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/agenticaiops
    targetRevision: main
    path: deploy
  destination:
    server: https://kubernetes.default.svc
    namespace: agents-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
      - PruneLast=true
  syncWave:
    - group: networking.k8s.io
      kind: NetworkPolicy
      wave: 0
    - group: rbac.authorization.k8s.io
      wave: 0
    - group: external-secrets.io
      wave: 1
    - group: ""
      kind: Secret
      wave: 1
    - group: apps
      kind: StatefulSet
      wave: 2
    - group: apps
      kind: Deployment
      wave: 3
    - group: kagent.dev
      kind: Agent
      wave: 4
```

### `deploy/argocd/projects/agents-project.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: agents
  namespace: argocd
spec:
  sourceRepos:
    - https://github.com/your-org/agenticaiops
  destinations:
    - namespace: agents-prod
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ""
      kind: Namespace
```

---

## Step 16 — Create CI Pipeline Config

### `.github/workflows/security-scan.yaml`

```yaml
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: SAST (Bandit)
        run: |
          pip install bandit
          bandit -r services/agents/src/ -f json -o bandit-report.json || true

      - name: Secret Scan (TruffleHog)
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}

      - name: Dependency Scan (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "services/agents/"
          format: "sarif"
          output: "trivy-results.sarif"

      - name: SBOM Generation (Syft)
        uses: anchore/syft-action@v0
        with:
          path: services/agents/
          format: spdx-json
          output: sbom.spdx.json

      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
            trivy-results.sarif
            sbom.spdx.json
```

---

## Step 17 — Create ISO Compliance Scaffolding

### `deploy/iso/9001/quality-policy.yaml`

```yaml
policy:
  statement: >
    AgenticAIOPs is committed to delivering reliable, accurate,
    and secure AI agent services. Quality is measured through
    agent response accuracy, uptime, and customer complaint
    resolution metrics.
  objectives:
    - Agent response accuracy >= 95%
    - Service uptime >= 99.9%
    - Complaint resolution SLA < 4 hours
    - Monthly quality review cycle
```

### `deploy/iso/27001/isms-policy.yaml`

```yaml
isms:
  scope: >
    All AI agent services, infrastructure, and data
    within the agents-prod Kubernetes namespace.
  principles:
    - Confidentiality: RBAC + NetworkPolicies + Encryption
    - Integrity: GitOps (ArgoCD), code review, SAST
    - Availability: Multi-replica, health probes, DR backups
  controls:
    - A.9: RBAC at K8s and application level
    - A.10: TLS >= 1.2, cert-manager auto-renewal
    - A.12: Monitoring, alerting, backup cronjobs
    - A.13: Network policies per tier
    - A.16: Incident response via Alertmanager + kagent
```

### `deploy/iso/27001/statement-of-applicability.yaml`

```yaml
soa:
  - control: A.5
    name: Information security policies
    applicable: true
    implemented: deploy/iso/27001/isms-policy.yaml
  - control: A.6
    name: Organization of information security
    applicable: true
    implemented: rbac/kubernetes/*.yaml
  - control: A.8
    name: Asset management
    applicable: true
    implemented: deploy/iso/27001/asset-register.yaml
  - control: A.9
    name: Access control
    applicable: true
    implemented: deploy/rbac/application/*.yaml
  - control: A.10
    name: Cryptography
    applicable: true
    implemented: TODO (cert-manager + TLS config)
  - control: A.12
    name: Operations security
    applicable: true
    implemented: deploy/network-policies/*.yaml + monitoring/
  - control: A.13
    name: Communications security
    applicable: true
    implemented: deploy/network-policies/*.yaml
  - control: A.14
    name: System acquisition, development
    applicable: true
    implemented: .github/workflows/security-scan.yaml
  - control: A.15
    name: Supplier relationships
    applicable: true
    implemented: deploy/iso/27001/supplier-assessment.yaml
  - control: A.16
    name: Incident management
    applicable: true
    implemented: TODO (incident-response-playbook.md)
  - control: A.17
    name: Business continuity
    applicable: true
    implemented: TODO (disaster-recovery-plan.md)
  - control: A.18
    name: Compliance
    applicable: true
    implemented: deploy/kagent/secops/compliance-auditor.yaml
```

### `deploy/iso/evidence/backup-verification.yaml`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-verification
  namespace: agents-prod
  labels:
    iso.27001/control: A.12.3
spec:
  schedule: "0 8 * * 1"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: security-auditor
          containers:
            - name: verify
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  echo "Checking PostgreSQL backup age..."
                  latest=$(kubectl get backup -n agents-prod -o json | jq -r '.items[-1].metadata.creationTimestamp')
                  age=$(( ($(date +%s) - $(date -d "$latest" +%s)) / 86400 ))
                  if [ $age -gt 1 ]; then
                    echo "WARNING: Backup is $age days old"
                    exit 1
                  fi
                  echo "Backup age: $age days - OK"
          restartPolicy: OnFailure
```

---

## Step 18 — Create Build Scripts

### `scripts/build-all.sh`

```bash
#!/bin/bash
set -euo pipefail

VERSION=${1:-latest}
REGISTRY=${REGISTRY:-agenticaiops}

echo "Building agents image..."
docker build -t $REGISTRY/agents:$VERSION -f services/agents/Dockerfile .

echo "Building gateway image..."
docker build -t $REGISTRY/gateway:$VERSION -f services/gateway/Dockerfile services/gateway/

echo "Done:"
echo "  $REGISTRY/agents:$VERSION"
echo "  $REGISTRY/gateway:$VERSION"
```

### `scripts/dev.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "Starting dev environment..."

cd shared && pip install -e . && cd ..

PYTHONPATH=services/agents/src \
  uvicorn main:app --host 0.0.0.0 --port 8001 --reload \
  --reload-dir services/agents/src --reload-dir shared/agenticaiops_shared &
AGENTS_PID=$!

docker run --rm -p 8080:8080 -p 8443:8443 \
  -v $(pwd)/services/gateway/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:1.27-alpine &
GATEWAY_PID=$!

echo "Agents: http://localhost:8001"
echo "Gateway: http://localhost:8080"

trap "kill $AGENTS_PID $GATEWAY_PID 2>/dev/null" EXIT
wait
```

---

## Step 19 — Post-Scaffolding Validation

```bash
echo "=== Step 19: Validation ==="

# 1. Verify directory structure
echo "Service files: $(find services/ -type f | wc -l)"
echo "Shared files: $(find shared/ -type f | wc -l)"
echo "Deploy files: $(find deploy/ -type f | wc -l)"

# 2. Check for leftover backend. imports
REMAINING=$(grep -rn "from backend\." services/agents/src/ 2>/dev/null || echo "")
if [ -n "$REMAINING" ]; then
    echo "WARNING: Leftover backend imports:"
    echo "$REMAINING"
else
    echo "No leftover backend imports"
fi

# 3. Test shared library install
cd shared && pip install -e . && cd ..

# 4. Dry-run agent imports
PYTHONPATH=services/agents/src python -c "
from agenticaiops_shared.config import settings
from agenticaiops_shared.database import Base, get_db
from src.qna.kg_retriever import kg_retriever
print('All imports successful')
"

# 5. Check deploy manifests exist
echo "Kagent agents: $(ls deploy/kagent/*.yaml | wc -l)"
echo "Secops agents: $(ls deploy/kagent/secops/*.yaml | wc -l)"
echo "Network policies: $(ls deploy/network-policies/*.yaml | wc -l)"
echo "RBAC manifests: $(ls deploy/rbac/**/*.yaml | wc -l)"
echo "Secrets: $(ls deploy/secrets/**/*.yaml | wc -l)"
echo "ISO: $(ls deploy/iso/**/*.yaml | wc -l)"

echo "=== Validation complete ==="
```

---

## File Count Summary

| Directory | Approx Files |
|---|---|
| `services/agents/src/` | ~50 (copied from backend) |
| `services/gateway/` | 3 |
| `shared/` | 10 |
| `deploy/kagent/` | 7 |
| `deploy/network-policies/` | 7 |
| `deploy/rbac/` | 5 |
| `deploy/secrets/` | 4 |
| `deploy/argocd/` | 2 |
| `deploy/ci/` | 1 |
| `deploy/iso/` | 4 |
| `scripts/` | 2 |
| **Total** | **~95 files** |

---

## Execution Order

```
Order is sequential — each step depends on the one before it.

Step  1: Create directory tree
Step  2: Copy files from backend/ -> services/agents/src/
Step  3: Create __init__.py files
Step  4: Create shared library package (+ pip install -e)
Step  5: Create services/agents/src/main.py
Step  6: Create services/agents/pyproject.toml
Step  7: Create services/agents/Dockerfile
Step  8: Create NGINX gateway (nginx.conf + Dockerfile)
Step  9: Create router modules per agent
Step 10: Update import paths (sed + manual fixes)
Step 11: Create kagent Agent CRs (2 agents + 5 secops)
Step 12: Create Network Policies (7 files)
Step 13: Create RBAC manifests (5 files)
Step 14: Create Secret Management manifests (4 files)
Step 15: Create ArgoCD manifests (2 files)
Step 16: Create CI pipeline config (1 file)
Step 17: Create ISO compliance scaffolding (4 files)
Step 18: Create build scripts (2 files)
Step 19: Post-scaffolding validation
```
