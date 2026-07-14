import kopf
import logging
from kubernetes import client, config

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────

def _load_kube():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def _labels(name, component):
    return {
        "app.kubernetes.io/name": name,
        "app.kubernetes.io/component": component,
        "app.kubernetes.io/part-of": "agenticaiops",
        "app.kubernetes.io/managed-by": "kopf",
    }


def _build_env(raw_env):
    """Convert CRD env (list of {name, value?, valueFrom?}) to V1EnvVar list."""
    if not raw_env:
        return []
    out = []
    for item in raw_env:
        var = client.V1EnvVar(name=item["name"])
        if "value" in item:
            var.value = item["value"]
        if "valueFrom" in item:
            src = item["valueFrom"]
            vf = client.V1EnvVarSource()
            if "configMapKeyRef" in src:
                vf.config_map_key_ref = client.V1ConfigMapKeySelector(
                    name=src["configMapKeyRef"]["name"],
                    key=src["configMapKeyRef"]["key"],
                    optional=src["configMapKeyRef"].get("optional", False),
                )
            if "secretKeyRef" in src:
                vf.secret_key_ref = client.V1SecretKeySelector(
                    name=src["secretKeyRef"]["name"],
                    key=src["secretKeyRef"]["key"],
                    optional=src["secretKeyRef"].get("optional", False),
                )
            var.value_from = vf
        out.append(var)
    return out


def _build_resources(raw):
    if not raw:
        return None
    return client.V1ResourceRequirements(
        requests={
            "cpu": raw.get("requests", {}).get("cpu", "100m"),
            "memory": raw.get("requests", {}).get("memory", "256Mi"),
        },
        limits={
            "cpu": raw.get("limits", {}).get("cpu"),
            "memory": raw.get("limits", {}).get("memory"),
        } if raw.get("limits") else None,
    )


def _build_volumes(raw_volumes):
    """Convert CRD extraVolumes to K8s Volume + VolumeMount lists."""
    if not raw_volumes:
        return [], []
    vols, mounts = [], []
    for v in raw_volumes:
        name = v["name"]
        read_only = v.get("readOnly", True)
        mounts.append(client.V1VolumeMount(
            name=name,
            mount_path=v["mountPath"],
            sub_path=v.get("subPath"),
            read_only=read_only,
        ))
        vol_src = client.V1Volume()
        if "persistentVolumeClaim" in v:
            vol_src.persistent_volume_claim = client.V1PersistentVolumeClaimVolumeSource(
                claim_name=v["persistentVolumeClaim"]["claimName"],
                read_only=read_only,
            )
        elif "configMap" in v:
            vol_src.config_map = client.V1ConfigMapVolumeSource(
                name=v["configMap"]["name"],
                items=[client.V1KeyToPath(key=i["key"], path=i["path"])
                       for i in v["configMap"].get("items", [])],
            )
        elif "secret" in v:
            vol_src.secret = client.V1SecretVolumeSource(
                secret_name=v["secret"]["secretName"],
                items=[client.V1KeyToPath(key=i["key"], path=i["path"])
                       for i in v["secret"].get("items", [])],
            )
        else:
            continue
        vols.append(client.V1Volume(name=name, **{k: v for k, v in vol_src.to_dict().items() if v}))
    return vols, mounts


# ── Reconcilers ──────────────────────────────────────────────────────────

def reconcile_agent(namespace, agent_name, spec, image, image_pull_policy, pull_secrets):
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    autoscaling_v1 = client.AutoscalingV1Api()
    policy_v1 = client.PolicyV1Api()

    labels = _labels(agent_name, "agent")
    en = spec.get("entrypoint")
    port = spec.get("servicePort", 8000)
    replicas = spec.get("replicas", {})
    min_replicas = replicas.get("min", 1)
    hpa_enabled = "max" in replicas
    resources = _build_resources(spec.get("resources"))
    env = _build_env(spec.get("env"))
    extra_vols, extra_mounts = _build_volumes(spec.get("extraVolumes"))
    probe_path = spec.get("probePath", "/health")
    grace = spec.get("terminationGracePeriodSeconds", 30)

    container = client.V1Container(
        name=f"{agent_name}-agent",
        image=image,
        image_pull_policy=image_pull_policy,
        ports=[client.V1ContainerPort(container_port=port)],
        command=["uvicorn"],
        args=[en, "--host", "0.0.0.0", "--port", str(port)],
        env=env or None,
        resources=resources,
        volume_mounts=extra_mounts or None,
        liveness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path=probe_path, port=port),
            initial_delay_seconds=5,
            period_seconds=15,
        ),
        readiness_probe=client.V1Probe(
            http_get=client.V1HTTPGetAction(path=probe_path, port=port),
            initial_delay_seconds=3,
            period_seconds=10,
        ),
        termination_message_policy="File",
    )

    pod_spec = client.V1PodSpec(
        containers=[container],
        termination_grace_period_seconds=grace,
        image_pull_secrets=pull_secrets,
        volumes=extra_vols or None,
    )

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=f"{agent_name}-agent",
            namespace=namespace,
            labels=labels,
        ),
        spec=client.V1DeploymentSpec(
            replicas=min_replicas,
            selector=client.V1LabelSelector(match_labels={"app.kubernetes.io/name": agent_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=pod_spec,
            ),
            strategy=client.V1DeploymentStrategy(
                type="RollingUpdate",
                rolling_update=client.V1RollingUpdateDeployment(
                    max_unavailable=0,
                    max_surge=1,
                ),
            ),
        ),
    )

    # Deployment
    try:
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info("Created deployment for agent %s", agent_name)
    except client.exceptions.ApiException as e:
        if e.status == 409:
            apps_v1.patch_namespaced_deployment(
                name=f"{agent_name}-agent",
                namespace=namespace,
                body=deployment,
            )
            logger.info("Updated deployment for agent %s", agent_name)
        else:
            raise

    # Service
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=f"{agent_name}-agent",
            namespace=namespace,
            labels=labels,
        ),
        spec=client.V1ServiceSpec(
            selector={"app.kubernetes.io/name": agent_name},
            ports=[client.V1ServicePort(
                port=port,
                target_port=port,
                protocol="TCP",
            )],
        ),
    )
    try:
        core_v1.create_namespaced_service(namespace=namespace, body=svc)
        logger.info("Created service for agent %s", agent_name)
    except client.exceptions.ApiException as e:
        if e.status == 409:
            core_v1.patch_namespaced_service(
                name=f"{agent_name}-agent",
                namespace=namespace,
                body=svc,
            )

    # HPA
    if hpa_enabled:
        hpa = client.V1HorizontalPodAutoscaler(
            metadata=client.V1ObjectMeta(
                name=f"{agent_name}-agent-hpa",
                namespace=namespace,
                labels=labels,
            ),
            spec=client.V1HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V1CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=f"{agent_name}-agent",
                ),
                min_replicas=min_replicas,
                max_replicas=replicas["max"],
                target_cpu_utilization_percentage=replicas.get("targetCPU", 75),
            ),
        )
        try:
            autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(namespace=namespace, body=hpa)
        except client.exceptions.ApiException as e:
            if e.status == 409:
                autoscaling_v1.patch_namespaced_horizontal_pod_autoscaler(
                    name=f"{agent_name}-agent-hpa",
                    namespace=namespace,
                    body=hpa,
                )

    # PDB
    pdb = spec.get("pdb")
    if pdb:
        pdb_body = client.V1PodDisruptionBudget(
            metadata=client.V1ObjectMeta(
                name=f"{agent_name}-agent-pdb",
                namespace=namespace,
                labels=labels,
            ),
            spec=client.V1PodDisruptionBudgetSpec(
                min_available=pdb.get("minAvailable"),
                max_unavailable=pdb.get("maxUnavailable"),
                selector=client.V1LabelSelector(
                    match_labels={"app.kubernetes.io/name": agent_name},
                ),
            ),
        )
        try:
            policy_v1.create_namespaced_pod_disruption_budget(namespace=namespace, body=pdb_body)
        except client.exceptions.ApiException as e:
            if e.status == 409:
                policy_v1.patch_namespaced_pod_disruption_budget(
                    name=f"{agent_name}-agent-pdb",
                    namespace=namespace,
                    body=pdb_body,
                )


def reconcile_gateway(namespace, spec):
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    gw = spec.get("gateway", {})
    if not gw.get("enabled", True):
        return

    labels = _labels("nginx-gateway", "gateway")
    gw_image = gw.get("image", "nginx:1.27-alpine")
    replicas = gw.get("replicas", 2)
    resources = _build_resources(gw.get("resources"))

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name="nginx-gateway",
            namespace=namespace,
            labels=labels,
        ),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app.kubernetes.io/name": "nginx-gateway"}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=client.V1PodSpec(containers=[
                    client.V1Container(
                        name="nginx",
                        image=gw_image,
                        ports=[client.V1ContainerPort(container_port=8080)],
                        resources=resources,
                    ),
                ]),
            ),
        ),
    )

    try:
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info("Created gateway deployment")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            apps_v1.patch_namespaced_deployment(namespace=namespace, name="nginx-gateway", body=deployment)

    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name="nginx-gateway", namespace=namespace, labels=labels),
        spec=client.V1ServiceSpec(
            selector={"app.kubernetes.io/name": "nginx-gateway"},
            ports=[client.V1ServicePort(port=8000, target_port=8080)],
        ),
    )
    try:
        core_v1.create_namespaced_service(namespace=namespace, body=svc)
    except client.exceptions.ApiException as e:
        if e.status == 409:
            core_v1.patch_namespaced_service(namespace=namespace, name="nginx-gateway", body=svc)


def reconcile_frontend(namespace, spec):
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

    fe = spec.get("frontend", {})
    if not fe.get("enabled", True):
        return

    labels = _labels("agenticaiops-frontend", "frontend")
    fe_image = fe.get("image")
    if not fe_image:
        logger.warning("Frontend enabled but no image specified — skipping")
        return
    replicas = fe.get("replicas", 2)
    resources = _build_resources(fe.get("resources"))
    env = _build_env(fe.get("env"))

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name="agenticaiops-frontend",
            namespace=namespace,
            labels=labels,
        ),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app.kubernetes.io/name": "agenticaiops-frontend"}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=client.V1PodSpec(containers=[
                    client.V1Container(
                        name="frontend",
                        image=fe_image,
                        ports=[client.V1ContainerPort(container_port=3000)],
                        env=env or None,
                        resources=resources,
                    ),
                ]),
            ),
        ),
    )

    try:
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info("Created frontend deployment")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            apps_v1.patch_namespaced_deployment(namespace=namespace, name="agenticaiops-frontend", body=deployment)

    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name="agenticaiops-frontend", namespace=namespace, labels=labels),
        spec=client.V1ServiceSpec(
            selector={"app.kubernetes.io/name": "agenticaiops-frontend"},
            ports=[client.V1ServicePort(port=3000, target_port=3000)],
        ),
    )
    try:
        core_v1.create_namespaced_service(namespace=namespace, body=svc)
    except client.exceptions.ApiException as e:
        if e.status == 409:
            core_v1.patch_namespaced_service(namespace=namespace, name="agenticaiops-frontend", body=svc)


# ── Ingress / Route ──────────────────────────────────────────────────────

def reconcile_ingress(namespace, spec):
    networking_v1 = client.NetworkingV1Api()
    ingress_type = spec.get("ingressType", "ingress")

    for owner, cfg in [("gateway", spec.get("gateway", {})),
                       ("frontend", spec.get("frontend", {}))]:
        ing = cfg.get("ingress", {})
        if not ing.get("enabled", True):
            continue
        host = ing.get("host")
        if not host:
            continue
        svc_name = "nginx-gateway" if owner == "gateway" else "agenticaiops-frontend"
        svc_port = 8000 if owner == "gateway" else 3000
        type_override = ing.get("type", ingress_type)

        labels = _labels(f"{owner}-ingress", "networking")
        name = f"platform-{owner}"

        if type_override == "route":
            continue  # OpenShift Route — not implemented yet

        ingress = client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels=labels,
                annotations={
                    "traefik.ingress.kubernetes.io/router.entrypoints": "web",
                },
            ),
            spec=client.V1IngressSpec(
                ingress_class_name=ing.get("className", "traefik"),
                rules=[client.V1IngressRule(
                    host=host,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="/",
                            path_type="Prefix",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=svc_name,
                                    port=client.V1ServiceBackendPort(number=svc_port),
                                ),
                            ),
                        )],
                    ),
                )],
            ),
        )
        try:
            networking_v1.create_namespaced_ingress(namespace=namespace, body=ingress)
        except client.exceptions.ApiException as e:
            if e.status == 409:
                networking_v1.patch_namespaced_ingress(namespace=namespace, name=name, body=ingress)


# ── Status ────────────────────────────────────────────────────────────────

def update_status(namespace, name, body):
    api = client.CustomObjectsApi()
    try:
        api.patch_namespaced_custom_object_status(
            group="platform.agenticaiops.io",
            version="v1",
            namespace=namespace,
            plural="agentplatforms",
            name=name,
            body=body,
        )
    except client.exceptions.ApiException:
        logger.exception("Failed to update status for %s/%s", namespace, name)


# ── Kopf Handlers ─────────────────────────────────────────────────────────

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.INFO
    _load_kube()


@kopf.on.create("platform.agenticaiops.io", "v1", "agentplatforms")
@kopf.on.update("platform.agenticaiops.io", "v1", "agentplatforms")
def reconcile(spec, name, namespace, logger, **_):
    image = spec.get("image", "localhost:5000/agenticaiops-backend:v1")
    image_pull_policy = spec.get("imagePullPolicy", "IfNotPresent")
    pull_secrets_raw = spec.get("imagePullSecrets")
    pull_secrets = (
        [client.V1LocalObjectReference(name=s["name"]) for s in pull_secrets_raw]
        if pull_secrets_raw else None
    )

    # Reconcile agents
    agent_statuses = {}
    for agent_name, agent_spec in spec.get("agents", {}).items():
        if not agent_spec.get("enabled", True):
            continue
        reconcile_agent(namespace, agent_name, agent_spec, image, image_pull_policy, pull_secrets)
        agent_statuses[agent_name] = {"ready": 0, "desired": agent_spec.get("replicas", {}).get("min", 1)}

    # Reconcile gateway
    reconcile_gateway(namespace, spec)

    # Reconcile frontend
    reconcile_frontend(namespace, spec)

    # Reconcile ingress
    reconcile_ingress(namespace, spec)

    # Update status
    update_status(namespace, name, {
        "status": {
            "observedGeneration": 1,
            "conditions": [
                {
                    "type": "Ready",
                    "status": "True",
                    "reason": "ReconciliationComplete",
                    "message": "All resources reconciled successfully",
                    "lastTransitionTime": None,
                },
            ],
            "agentStatuses": agent_statuses,
        },
    })

    return {"reconciled": True}


@kopf.on.delete("platform.agenticaiops.io", "v1", "agentplatforms")
def delete(spec, name, namespace, logger, **_):
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    for agent_name in spec.get("agents", {}):
        try:
            apps_v1.delete_namespaced_deployment(name=f"{agent_name}-agent", namespace=namespace)
        except client.exceptions.ApiException:
            pass
        try:
            core_v1.delete_namespaced_service(name=f"{agent_name}-agent", namespace=namespace)
        except client.exceptions.ApiException:
            pass

    for resource in ["nginx-gateway", "agenticaiops-frontend"]:
        try:
            apps_v1.delete_namespaced_deployment(name=resource, namespace=namespace)
        except client.exceptions.ApiException:
            pass
        try:
            core_v1.delete_namespaced_service(name=resource, namespace=namespace)
        except client.exceptions.ApiException:
            pass


if __name__ == "__main__":
    kopf.run()
