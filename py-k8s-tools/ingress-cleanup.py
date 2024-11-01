from kubernetes import client, config
from typing import List

def list_ingresses(class_name: str) -> List[str]:
    """
    Lists all Ingress objects with specified ingressClassName.
    Returns list of 'namespace/name'
    """
    out = []

    # for all ingresses across all namespaces
    for ing in client.NetworkingV1Api().list_ingress_for_all_namespaces().items:
        if ing.spec.ingress_class_name == class_name:
            name, namespace = ing.metadata.name, ing.metadata.namespace
            out.append(f"{namespace}/{name}")

    return out

def delete_ingresses(class_name: str) -> int:
    """
    Deletes all ingress objects with a specified ingressClassName
    """
    cnt = 0

    v1 = client.NetworkingV1Api()
    # List all ingresses across all namespaces
    for ing in v1.list_ingress_for_all_namespaces().items:
        if ing.spec.ingress_class_name == class_name:
            name, namespace = ing.metadata.name, ing.metadata.namespace
            v1.delete_namespaced_ingress(
                name=name,
                namespace=namespace
            )
            cnt = cnt + 1

    return cnt

def main():
    config.load_kube_config()
    class_name = "tailscale"
    i = list_ingresses(class_name)
    print(f"deleting ingresses ({class_name}): {','.join(i)}")
    cnt = delete_ingresses(class_name)
    print(f"deleted {cnt} ingresses")

main()
