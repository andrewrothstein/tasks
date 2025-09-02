"""CLI for vCluster ArgoCD Enroller operator."""

import sys
import logging
from pathlib import Path
from typing import Optional, Literal

import cyclopts
import kopf
from rich.console import Console
from rich.logging import RichHandler

from . import __version__

console = Console()
app = cyclopts.App(
    name="vcluster-argocd-enroller",
    version=__version__,
    help="Kubernetes operator that automatically enrolls vCluster instances in ArgoCD",
)


def setup_logging(level: str = "INFO", rich: bool = True) -> None:
    """Configure logging with optional rich output."""
    log_level = getattr(logging, level.upper())

    if rich:
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, rich_tracebacks=True)],
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


@app.default
def run(
    *,
    namespace: Optional[str] = None,
    dev: bool = False,
    verbose: bool = False,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    standalone: bool = False,
    priority: int = 0,
    peering_name: Optional[str] = None,
    clusterwide: bool = True,
) -> None:
    """Run the vCluster ArgoCD enrollment operator.

    Parameters
    ----------
    namespace : str, optional
        Namespace to watch for vClusters (default: all namespaces)
    dev : bool
        Run in development mode with auto-reload
    verbose : bool
        Enable verbose output (sets log level to DEBUG)
    log_level : str
        Logging level (DEBUG, INFO, WARNING, ERROR)
    standalone : bool
        Run in standalone mode (no peering)
    priority : int
        Operator priority for peering
    peering_name : str, optional
        Custom peering name for multiple operators
    clusterwide : bool
        Watch cluster-wide (default: True)
    """
    if verbose:
        log_level = "DEBUG"

    setup_logging(log_level)

    console.print(f"[bold green]vCluster ArgoCD Enroller v{__version__}[/bold green]")
    console.print(f"[dim]Running in {'development' if dev else 'production'} mode[/dim]")

    if namespace:
        console.print(f"[yellow]Watching namespace:[/yellow] {namespace}")
        clusterwide = False
    else:
        console.print("[yellow]Watching:[/yellow] all namespaces")

    # Import operator module to register handlers
    from . import operator  # noqa: F401

    # Build kopf args
    kopf_args = []

    if namespace and not clusterwide:
        kopf_args.extend(["--namespace", namespace])

    if dev:
        kopf_args.append("--dev")

    if verbose:
        kopf_args.append("--verbose")

    if standalone:
        kopf_args.append("--standalone")

    if priority:
        kopf_args.extend(["--priority", str(priority)])

    if peering_name:
        kopf_args.extend(["--peering", peering_name])

    # Run kopf
    import kopf.cli
    sys.argv = ["kopf", "run", "-m", "vcluster_argocd_enroller.operator"] + kopf_args

    if clusterwide:
        sys.argv.append("--clusterwide")

    console.print("[green]Starting operator...[/green]")
    sys.exit(kopf.cli.main())


@app.command
def check(
    *,
    namespace: Optional[str] = None,
    show_secrets: bool = False,
) -> None:
    """Check for existing vClusters and their ArgoCD enrollment status.

    Parameters
    ----------
    namespace : str, optional
        Namespace to check (default: all namespaces)
    show_secrets : bool
        Show secret details (default: False)
    """
    from kubernetes import client, config
    from rich.table import Table

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # Find vCluster StatefulSets
    if namespace:
        statefulsets = apps_v1.list_namespaced_stateful_set(
            namespace=namespace,
            label_selector="app=vcluster"
        )
    else:
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces(
            label_selector="app=vcluster"
        )

    if not statefulsets.items:
        console.print("[yellow]No vClusters found[/yellow]")
        return

    # Create table
    table = Table(title="vCluster Status")
    table.add_column("Namespace", style="cyan")
    table.add_column("vCluster", style="green")
    table.add_column("Ready", style="yellow")
    table.add_column("Secret", style="blue")
    table.add_column("ArgoCD Secret", style="magenta")

    for sts in statefulsets.items:
        ns = sts.metadata.namespace
        name = sts.metadata.name

        # Extract vcluster name
        vcluster_name = name.replace('vcluster-', '').rsplit('-', 1)[0]

        # Check readiness
        ready = f"{sts.status.ready_replicas or 0}/{sts.spec.replicas}"

        # Check for vcluster secret
        vc_secret_name = f"vc-{vcluster_name}"
        try:
            v1.read_namespaced_secret(name=vc_secret_name, namespace=ns)
            vc_secret_status = "✓"
        except client.exceptions.ApiException:
            vc_secret_status = "✗"

        # Check for ArgoCD secret
        argocd_secret_name = f"vcluster-{vcluster_name}"
        try:
            v1.read_namespaced_secret(name=argocd_secret_name, namespace="argocd")
            argocd_secret_status = "✓"
        except client.exceptions.ApiException:
            argocd_secret_status = "✗"

        table.add_row(ns, vcluster_name, ready, vc_secret_status, argocd_secret_status)

    console.print(table)

    if show_secrets:
        console.print("\n[bold]Secret Details:[/bold]")
        for sts in statefulsets.items:
            ns = sts.metadata.namespace
            name = sts.metadata.name
            vcluster_name = name.replace('vcluster-', '').rsplit('-', 1)[0]

            console.print(f"\n[cyan]{ns}/{vcluster_name}:[/cyan]")
            console.print(f"  vCluster Secret: vc-{vcluster_name}")
            console.print(f"  ArgoCD Secret: vcluster-{vcluster_name}")


@app.command
def enroll(
    vcluster_name: str,
    namespace: str = "default",
    *,
    force: bool = False,
) -> None:
    """Manually enroll a vCluster in ArgoCD.

    Parameters
    ----------
    vcluster_name : str
        Name of the vCluster to enroll
    namespace : str
        Namespace where vCluster is deployed
    force : bool
        Force re-enrollment even if already exists
    """
    from kubernetes import client, config
    import json
    import base64

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()

    # Check for existing ArgoCD secret
    argocd_secret_name = f"vcluster-{vcluster_name}"

    if not force:
        try:
            v1.read_namespaced_secret(name=argocd_secret_name, namespace="argocd")
            console.print(f"[yellow]vCluster {vcluster_name} already enrolled in ArgoCD[/yellow]")
            console.print("[dim]Use --force to re-enroll[/dim]")
            return
        except client.exceptions.ApiException:
            pass

    # Read vCluster secret
    vc_secret_name = f"vc-{vcluster_name}"
    try:
        vc_secret = v1.read_namespaced_secret(name=vc_secret_name, namespace=namespace)
    except client.exceptions.ApiException as e:
        console.print(f"[red]Failed to read vCluster secret {vc_secret_name}: {e}[/red]")
        sys.exit(1)

    # Create ArgoCD secret
    def encode(s):
        return base64.b64encode(s.encode('utf-8')).decode('utf-8')

    argocd_secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": argocd_secret_name,
            "namespace": "argocd",
            "labels": {
                "argocd.argoproj.io/secret-type": "cluster",
                "vcluster-operator": "true"
            }
        },
        "data": {
            "name": encode(vcluster_name),
            "server": encode(f"https://{vcluster_name}.{namespace}.svc.cluster.local"),
            "config": encode(json.dumps({
                "tlsClientConfig": {
                    "caData": vc_secret.data["certificate-authority"],
                    "certData": vc_secret.data["client-certificate"],
                    "keyData": vc_secret.data["client-key"],
                    "insecure": False
                }
            }))
        }
    }

    # Create or replace the secret
    if force:
        try:
            v1.delete_namespaced_secret(name=argocd_secret_name, namespace="argocd")
            console.print(f"[yellow]Deleted existing ArgoCD secret[/yellow]")
        except client.exceptions.ApiException:
            pass

    try:
        v1.create_namespaced_secret(namespace="argocd", body=argocd_secret)
        console.print(f"[green]✓ Successfully enrolled vCluster {vcluster_name} in ArgoCD[/green]")
    except client.exceptions.ApiException as e:
        console.print(f"[red]Failed to create ArgoCD secret: {e}[/red]")
        sys.exit(1)


@app.command
def unenroll(
    vcluster_name: str,
    *,
    confirm: bool = False,
) -> None:
    """Remove a vCluster from ArgoCD.

    Parameters
    ----------
    vcluster_name : str
        Name of the vCluster to unenroll
    confirm : bool
        Skip confirmation prompt
    """
    from kubernetes import client, config

    if not confirm:
        response = console.input(f"[yellow]Remove {vcluster_name} from ArgoCD? [y/N]:[/yellow] ")
        if response.lower() != 'y':
            console.print("[dim]Cancelled[/dim]")
            return

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    argocd_secret_name = f"vcluster-{vcluster_name}"

    try:
        v1.delete_namespaced_secret(name=argocd_secret_name, namespace="argocd")
        console.print(f"[green]✓ Successfully removed vCluster {vcluster_name} from ArgoCD[/green]")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            console.print(f"[yellow]vCluster {vcluster_name} not found in ArgoCD[/yellow]")
        else:
            console.print(f"[red]Failed to remove ArgoCD secret: {e}[/red]")
            sys.exit(1)


@app.command
def test() -> None:
    """Run tests against the operator."""
    import subprocess

    console.print("[bold]Running tests...[/bold]")
    result = subprocess.run(["pytest", "tests/", "-v"], capture_output=False)
    sys.exit(result.returncode)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
