"""Delete Kubernetes Ingress objects by ingressClassName."""

from typing import Annotated

import cyclopts
from kubernetes import client, config

app = cyclopts.App(help="Delete Kubernetes Ingress objects by ingressClassName.")


def list_ingresses(class_name: str) -> list[tuple[str, str]]:
    """List all Ingress objects with specified ingressClassName."""
    out = []
    for ing in client.NetworkingV1Api().list_ingress_for_all_namespaces().items:
        if ing.spec.ingress_class_name == class_name:
            out.append((ing.metadata.namespace, ing.metadata.name))
    return out


def delete_ingress(namespace: str, name: str) -> None:
    """Delete a single ingress."""
    client.NetworkingV1Api().delete_namespaced_ingress(name=name, namespace=namespace)


@app.default
def main(
    class_name: Annotated[str, cyclopts.Parameter(help="Ingress class name to filter")] = "tailscale",
    dry_run: Annotated[bool, cyclopts.Parameter(help="List ingresses without deleting")] = False,
) -> None:
    """Delete all Ingress objects with the specified ingressClassName."""
    config.load_kube_config()
    ingresses = list_ingresses(class_name)

    if not ingresses:
        print(f"No ingresses found with class '{class_name}'")
        return

    print(f"Found {len(ingresses)} ingress(es) with class '{class_name}':")
    for ns, name in ingresses:
        print(f"  {ns}/{name}")

    if dry_run:
        print("Dry run - no ingresses deleted")
        return

    for ns, name in ingresses:
        delete_ingress(ns, name)
        print(f"Deleted {ns}/{name}")

    print(f"Deleted {len(ingresses)} ingress(es)")


if __name__ == "__main__":
    app()
