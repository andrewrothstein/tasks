import kopf
import kubernetes
import yaml
import json
import base64
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import logging

ARGOCD_NAMESPACE="argocd"

logger = logging.getLogger()

try:
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        logger.debug("Running in cluster, using in-cluster config")
        config.load_incluster_config()
    else:
        logger.debug("Running locally, using kubeconfig")
        config.load_kube_config()
except config.ConfigException as e:
    logger.error(f"Failed to load kubernetes config: {e}")
    raise kopf.PermanentError("Could not configure kubernetes client")

core_v1_api = client.CoreV1Api()
apps_v1_api = client.AppsV1Api()

def vc_name(statefulset_name: str) -> str:
    return statefulset_name.replace('vcluster-', '').rsplit('-', 1)[0]

def ar_secret_name(vcluster_name: str) -> str:
    return f"vcluster-{vcluster_name}"

def decode(d):
    return base64.b64decode(d).decode('utf-8')
def encode(s):
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')

def handle_vcluster_enrollment(
        statefulset_name: str,
        namespace: str,
        **kwargs
):
    logger.info(f"Processing vcluster enrollment for StatefulSet {namespace}/{statefulset_name}")

    vcluster_name = vc_name(statefulset_name)

    logger.info(f"Mapped StatefulSet {statefulset_name} to vcluster {vcluster_name}")

    vcluster_secret_name = f"vc-{vcluster_name}"
    logger.info(f"Extracting kubeconfig secret data for vcluster {namespace}/{vcluster_name} from {vcluster_secret_name} secret")

    try:
        vc_secret = core_v1_api.read_namespaced_secret(
            name=vcluster_secret_name,
            namespace=namespace
        )

        argocd_secret_name = ar_secret_name(vcluster_name)
        logger.info(f"Creating ArgoCD cluster secret {argocd_secret_name} for {vcluster_name} vcluster...")
        core_v1_api.create_namespaced_secret(
            ARGOCD_NAMESPACE,
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": argocd_secret_name,
                    "namespace": ARGOCD_NAMESPACE,
                    "labels": {
                        "argocd.argoproj.io/secret-type": "cluster",
                        "vcluster-operator": "true"
                    }
                },
                "data": {
                    "name": encode(vcluster_name),
                    "server": encode(f"https://{vcluster_name}.{namespace}.svc.cluster.local"),
                    "config": encode(yaml.dump({
                        "tlsClientConfig": {
                            "caData": decode(vc_secret.data["certificate-authority"]),
                            "certData": decode(vc_secret.data["client-certificate"]),
                            "keyData": decode(vc_secret.data["client-key"]),
                            "insecure": False
                        }
                    }))
                }
            }
        )
        logger.info(f"Successfully created ArgoCD cluster secret {argocd_secret_name} for vcluster {vcluster_name}")
        return {'status': 'Success'}

    except ApiException as e:
        logger.error(
            f"API error enrolling vcluster {namespace}/{vcluster_name}: {e}"
        )
        raise kopf.TemporaryError(
            f"Failed to enroll vcluster {namespace}/{vcluster_name}: {e}",
            delay=60
        )
    except (KeyError, IndexError, yaml.YAMLError) as e:
        logger.error(
            f"Improperly formed vcluster secret: {namespace}/{vcluster_secret_name}"
        )
        raise kopf.PermanentError(
            f"Failed to parse vcluster secret: {namespace}/{vcluster_secret_name}"
        )

    except kopf.TemporaryError as e:
        logger.warning(f"Temporary error enrolling vcluster: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to enroll vcluster {namespace}/{vcluster_name}: {e}")
        raise kopf.PermanentError(
            f"Failed to enroll vcluster in ArgoCD: {e}")

@kopf.on.create('statefulsets', labels={'app': 'vcluster'})
def vcluster_created(
        name,
        namespace,
        meta,
        spec,
        **kwargs
):
    """Handle vcluster StatefulSet creation"""
    statefulset_name = name
    logger.info(
        f"Detected new vcluster StatefulSet: {namespace}/{statefuleset_name}"
    )
    return handle_vcluster_enrollment(
        statefuleset_name,
        namespace,
        **kwargs
    )

@kopf.on.resume('statefulsets', labels={'app': 'vcluster'})
def vcluster_resumed(
        name,
        namespace,
        meta,
        spec,
        **kwargs
):
    """Handle existing vcluster StatefulSets when operator starts"""
    statefulset_name = name
    logger.info(
        f"Detected existing vcluster StatefulSet: {namespace}/{statefulset_name}"
    )
    return handle_vcluster_enrollment(
        name,
        namespace,
        **kwargs
    )

@kopf.on.delete('statefulsets', labels={'app': 'vcluster'})
def vcluster_deleted(
        name,
        namespace,
        **kwargs
):
    """Handle vcluster StatefulSet deletion"""
    statefulset_name = name
    logger.info(
        f"Detected vcluster StatefulSet deletion: {namespace}/{statefuleset_name}"
    )

    vcluster_name = vc_name(statefuleset_name)
    argocd_secret_name = ar_secret_name(vcluster_name)

    logger.info(f"Deleting ArgoCD cluster secret {argocd_secret_name} for {namespace}/{vcluster_name}")

    try:
        core_v1_api.delete_namespaced_secret(
            name=argocd_secret_name,
            namespace=ARGOCD_NAMESPACE
        )

        logger.info(
            f"Successfully deleted ArgoCD cluster secret {argocd_secret_name} for vcluster {namespace}/{vcluster_name}"
        )
        return {'status': 'Success'}

    except ApiException as e:
        if e.status == 404:
            logger.info(
                f"ArgoCD secret {argocd_secret_name} for vcluster {namespace}/{vcluster_name} not found"
            )
        else:
            logger.error(
                f"Failed to delete ArgoCD cluster secret for vcluster {namespace}/{vcluster_name}: {e}")
            raise kopf.PermanentError(
                f"Failed to delete ArgoCD cluster secret for vcluster {namespace}/{vcluster_name}: {e}"
            )
    except Exception as e:
        logger.error(
            f"Failed to remove vcluster {namespace}/{vcluster_name} from ArgoCD: {e}"
        )
        raise kopf.PermanentError(
            f"Failed to remove vcluster {namespace}/{vcluster_name} from ArgoCD: {e}"
        )
